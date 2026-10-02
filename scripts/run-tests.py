#!/usr/bin/env python3
"""Run Taurus scenarios through scripts/run-taurus.ps1."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_TAURUS = REPO_ROOT / "scripts" / "run-taurus.ps1"
MOCK_API_SERVER = REPO_ROOT / "scripts" / "mock-api-server.py"
MOCK_API_HEALTH_URL = "http://localhost:8000/get"
TAURUS_PYTHON = REPO_ROOT / ".venv-taurus" / "Scripts" / "python.exe"

DEFAULT_SCENARIOS = [
    "tests/api/test-api-load.yml",
    "tests/api/spike.yml",
    "tests/api/assertions.yml",
    "tests/api/test-api-sla.yml",
]

OPTIONAL_SCENARIOS = {
    "--include-jmeter": "tests/api/test-api-jmeter.yml",
    "--include-soak": "tests/api/soak.yml",
    "--include-stress": "tests/api/stress.yml",
}


def run_powershell(config: str) -> int:
    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(RUN_TAURUS),
        "-Mode",
        "standard",
        "-Config",
        config,
    ]

    print(f"\n=== Running: {config} ===", flush=True)
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    return result.returncode


def run_k6() -> int:
    cmd = ["k6", "run", "tests/api/test-api-k6.js"]
    print("\n=== Running: tests/api/test-api-k6.js (k6) ===", flush=True)
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    return result.returncode


def mock_api_is_ready() -> bool:
    try:
        with urllib.request.urlopen(MOCK_API_HEALTH_URL, timeout=1) as response:
            return response.status == 200
    except OSError:
        return False


def find_mock_api_python() -> Path:
    candidates = [Path(sys.executable), TAURUS_PYTHON]
    for executable in dict.fromkeys(candidates):
        if not executable.exists():
            continue
        result = subprocess.run(
            [str(executable), "-c", "import fastapi, uvicorn"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return executable
    raise RuntimeError("Mock API requires FastAPI and Uvicorn")


@contextmanager
def mock_api() -> Iterator[None]:
    if mock_api_is_ready():
        print("Using existing mock API on http://localhost:8000", flush=True)
        yield
        return

    if not MOCK_API_SERVER.exists():
        raise RuntimeError(f"Missing mock API server: {MOCK_API_SERVER}")

    python = find_mock_api_python()
    process = subprocess.Popen(
        [str(python), str(MOCK_API_SERVER)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if mock_api_is_ready():
                print("Started mock API on http://localhost:8000", flush=True)
                yield
                return
            if process.poll() is not None:
                raise RuntimeError(
                    f"Mock API exited during startup with code {process.returncode}"
                )
            time.sleep(0.25)
        raise RuntimeError("Mock API did not become ready on localhost:8000")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def shard_scenarios(
    scenarios: list[str], worker_count: int, worker_index: int
) -> list[str]:
    if worker_count <= 1:
        return scenarios

    return [
        scenario
        for index, scenario in enumerate(scenarios)
        if index % worker_count == worker_index
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Taurus API tests")
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run only Taurus health-check",
    )
    parser.add_argument(
        "--include-jmeter",
        action="store_true",
        help="Include tests/api/test-api-jmeter.yml",
    )
    parser.add_argument(
        "--include-soak",
        action="store_true",
        help="Include tests/api/soak.yml",
    )
    parser.add_argument(
        "--include-stress",
        action="store_true",
        help="Include tests/api/stress.yml (extreme load test)",
    )
    parser.add_argument(
        "--include-k6",
        action="store_true",
        help="Include tests/api/test-api-k6.js",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print selected scenarios and exit",
    )
    parser.add_argument(
        "--worker-count",
        type=int,
        default=1,
        help="Split Taurus scenarios across N workers",
    )
    parser.add_argument(
        "--worker-index",
        type=int,
        default=0,
        help="Zero-based worker index used with --worker-count",
    )
    return parser.parse_args()


def validate_worker_args(args: argparse.Namespace) -> str | None:
    if args.worker_count < 1:
        return "--worker-count must be >= 1"
    if args.worker_index < 0 or args.worker_index >= args.worker_count:
        return "--worker-index must be between 0 and worker-count - 1"
    return None


def select_scenarios(args: argparse.Namespace) -> list[str]:
    scenarios = list(DEFAULT_SCENARIOS)
    if args.include_jmeter:
        scenarios.append(OPTIONAL_SCENARIOS["--include-jmeter"])
    if args.include_soak:
        scenarios.append(OPTIONAL_SCENARIOS["--include-soak"])
    if args.include_stress:
        scenarios.append(OPTIONAL_SCENARIOS["--include-stress"])
    return shard_scenarios(scenarios, args.worker_count, args.worker_index)


def run_selected_scenarios(scenarios: list[str], include_k6: bool) -> int:
    for scenario in scenarios:
        code = run_powershell(scenario)
        if code != 0:
            print(f"FAILED: {scenario} (exit code {code})", file=sys.stderr)
            return code

    if include_k6:
        code = run_k6()
        if code != 0:
            print(
                f"FAILED: tests/api/test-api-k6.js (exit code {code})",
                file=sys.stderr,
            )
            return code

    print("\nAll selected scenarios completed successfully.")
    return 0


def main() -> int:
    if not RUN_TAURUS.exists():
        print(f"Missing script: {RUN_TAURUS}", file=sys.stderr)
        return 2

    args = parse_args()

    validation_error = validate_worker_args(args)
    if validation_error:
        print(validation_error, file=sys.stderr)
        return 2

    if args.health:
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(RUN_TAURUS),
            "-Mode",
            "health",
            "-Config",
            "tests/api/test-api-load.yml",
        ]
        return subprocess.run(cmd, cwd=REPO_ROOT, check=False).returncode

    scenarios = select_scenarios(args)

    if args.list:
        print(
            f"Selected Taurus scenarios for worker {args.worker_index + 1}/{args.worker_count}:"
        )
        for scenario in scenarios:
            print(f"- {scenario}")
        if args.include_k6:
            print("- tests/api/test-api-k6.js")
        return 0

    if not scenarios and not args.include_k6:
        print(
            f"No Taurus scenarios assigned to worker {args.worker_index + 1}/{args.worker_count}."
        )
        return 0

    try:
        with mock_api():
            return run_selected_scenarios(scenarios, args.include_k6)
    except RuntimeError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
