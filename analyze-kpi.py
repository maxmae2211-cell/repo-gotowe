#!/usr/bin/env python3
import argparse
from pathlib import Path

from jtl_metrics import extract_jtl_kpi


def find_latest_kpi(pattern: str) -> Path | None:
    candidates = sorted(Path(".").glob(pattern), reverse=True)
    for directory in candidates:
        if directory.is_dir():
            jtl_file = directory / "kpi.jtl"
            if jtl_file.exists():
                return jtl_file
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analiza KPI z pliku JTL")
    parser.add_argument(
        "--jtl",
        type=Path,
        help="Ścieżka do pliku kpi.jtl. Gdy brak, skrypt wybierze najnowszy katalog artefaktów.",
    )
    parser.add_argument(
        "--artifacts-pattern",
        default="2026-*",
        help="Wzorzec katalogów artefaktów Taurus do auto-wykrywania (domyślnie: 2026-*).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    jtl_file = args.jtl or find_latest_kpi(args.artifacts_pattern)

    if not jtl_file:
        print("❌ Nie znaleziono pliku kpi.jtl")
        return 1

    metrics = extract_jtl_kpi(jtl_file)
    if not metrics or not metrics["count"]:
        print(f"❌ Brak danych metryk w pliku: {jtl_file}")
        return 1

    print("=" * 70)
    print("✅ ANALIZA KPI")
    print("=" * 70)
    print(f"Plik:                 {jtl_file}")
    print(f"Liczba żądań:         {metrics['count']}")
    print(f"Błędy:                {metrics['failures']}")
    print(f"Sukcesy:              {metrics['successes']}")
    print("\nCzasy odpowiedzi (ms):")
    print(f"  Średni (AVG):       {metrics['avg_time']:.2f} ms")
    print(f"  Minimum:            {metrics['min_time']} ms")
    print(f"  Maximum:            {metrics['max_time']} ms")
    print(f"  P50 (Mediana):      {metrics['p50']} ms")
    print(f"  P90:                {metrics['p90']} ms")
    print(f"  P95:                {metrics['p95']} ms")
    print(f"  P99:                {metrics['p99']} ms")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
