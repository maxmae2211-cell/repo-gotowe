import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Python module or script, then keep terminal open until Enter is pressed."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--module", help="Python module to run, for example: bzt or pip")
    target.add_argument("--program", help="Python script path to run")
    parser.add_argument(
        "cmd_args",
        nargs=argparse.REMAINDER,
        help="Arguments for target command. Prefix with -- to separate wrapper args.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    forwarded = list(args.cmd_args)

    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    if args.module:
        cmd = [sys.executable, "-m", args.module, *forwarded]
    else:
        cmd = [sys.executable, args.program, *forwarded]

    print("[run_and_wait] Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    print(f"[run_and_wait] Exit code: {result.returncode}")

    try:
        input("[run_and_wait] Press Enter to end debug session...")
    except EOFError:
        # If stdin is not interactive, just exit with process status.
        pass

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
