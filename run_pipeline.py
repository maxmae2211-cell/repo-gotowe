#!/usr/bin/env python3
"""Uruchamia pełny pipeline analizy Taurus jedną komendą."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List


def run_step(step_name: str, command: List[str]) -> int:
    print(f"\n=== {step_name} ===")
    print(" ".join(command))
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"\n❌ Krok nieudany: {step_name} (exit={result.returncode})")
        return result.returncode
    print(f"✅ Krok zakończony: {step_name}")
    return 0


def parse_args() -> argparse.Namespace:
    default_pattern = f"{datetime.now().year}-*"
    parser = argparse.ArgumentParser(
        description="Pełny pipeline: analyze-kpi -> analyze_results -> generate_report"
    )
    parser.add_argument(
        "--jtl",
        type=Path,
        help="Ścieżka do konkretnego pliku kpi.jtl. Bez tego działa auto-wykrywanie.",
    )
    parser.add_argument(
        "--artifacts-pattern",
        default=default_pattern,
        help=(
            "Wzorzec katalogów artefaktów do auto-wykrywania "
            f"(domyślnie: {default_pattern})."
        ),
    )
    parser.add_argument(
        "--output",
        default="taurus-locust-report.html",
        help="Nazwa pliku wyjściowego raportu HTML.",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=0,
        help="Maksymalna dozwolona liczba błędów dla bramki jakości.",
    )
    parser.add_argument(
        "--max-avg-ms",
        type=float,
        default=None,
        help="Maksymalny dozwolony średni czas odpowiedzi w ms dla bramki jakości.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    python = sys.executable

    analyze_kpi_cmd = [python, "analyze-kpi.py"]
    analyze_results_cmd = [python, "analyze_results.py"]
    generate_report_cmd = [python, "generate_report.py", "--output", args.output]

    if args.jtl:
        analyze_kpi_cmd += ["--jtl", str(args.jtl)]
        analyze_results_cmd += ["--jtl", str(args.jtl)]
    else:
        analyze_kpi_cmd += ["--artifacts-pattern", args.artifacts_pattern]
        analyze_results_cmd += ["--artifacts-pattern", args.artifacts_pattern]
        generate_report_cmd += ["--artifacts-pattern", args.artifacts_pattern]

    analyze_kpi_cmd += ["--max-failures", str(args.max_failures)]
    if args.max_avg_ms is not None:
        analyze_kpi_cmd += ["--max-avg-ms", str(args.max_avg_ms)]

    for step_name, command in [
        ("Analiza KPI", analyze_kpi_cmd),
        ("Analiza szczegółowa", analyze_results_cmd),
        ("Generowanie raportu HTML", generate_report_cmd),
    ]:
        code = run_step(step_name, command)
        if code != 0:
            return code

    print("\n🎉 Pipeline zakończony poprawnie")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
