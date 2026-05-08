#!/usr/bin/env python3
"""Run Taurus scenarios through scripts/run-taurus.ps1."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_TAURUS = REPO_ROOT / "scripts" / "run-taurus.ps1"

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
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def run_k6() -> int:
    cmd = ["k6", "run", "tests/api/test-api-k6.js"]
    print("\n=== Running: tests/api/test-api-k6.js (k6) ===", flush=True)
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


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
    return parser.parse_args()


def main() -> int:
    if not RUN_TAURUS.exists():
        print(f"Missing script: {RUN_TAURUS}", file=sys.stderr)
        return 2

    args = parse_args()

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
        return subprocess.run(cmd, cwd=REPO_ROOT).returncode

    scenarios = list(DEFAULT_SCENARIOS)
    if args.include_jmeter:
        scenarios.append(OPTIONAL_SCENARIOS["--include-jmeter"])
    if args.include_soak:
        scenarios.append(OPTIONAL_SCENARIOS["--include-soak"])
    if args.include_stress:
        scenarios.append(OPTIONAL_SCENARIOS["--include-stress"])

    if args.list:
        print("Selected Taurus scenarios:")
        for scenario in scenarios:
            print(f"- {scenario}")
        if args.include_k6:
            print("- tests/api/test-api-k6.js")
        return 0

    for scenario in scenarios:
        code = run_powershell(scenario)
        if code != 0:
            print(f"FAILED: {scenario} (exit code {code})", file=sys.stderr)
            return code

    if args.include_k6:
        code = run_k6()
        if code != 0:
            print(f"FAILED: tests/api/test-api-k6.js (exit code {code})", file=sys.stderr)
            return code

    print("\nAll selected scenarios completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
