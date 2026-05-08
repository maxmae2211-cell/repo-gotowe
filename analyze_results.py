#!/usr/bin/env python3
"""
Analiza wyników Taurus Obciążeniowych
"""

import argparse
from collections import defaultdict
from datetime import datetime
import statistics
from pathlib import Path

from jtl_metrics import read_jtl_rows


def find_latest_kpi(pattern: str) -> Path | None:
    candidates = sorted(Path(".").glob(pattern), reverse=True)
    for directory in candidates:
        if directory.is_dir():
            jtl_file = directory / "kpi.jtl"
            if jtl_file.exists():
                return jtl_file
    return None


def parse_args(args=None) -> argparse.Namespace:
    default_pattern = f"{datetime.now().year}-*"
    parser = argparse.ArgumentParser(
        description="Szczegółowa analiza wyników z pliku kpi.jtl"
    )
    parser.add_argument(
        "--jtl",
        type=Path,
        help="Ścieżka do pliku kpi.jtl. Gdy brak, skrypt wybierze najnowszy katalog artefaktów.",
    )
    parser.add_argument(
        "--artifacts-pattern",
        default=default_pattern,
        help=(
            "Wzorzec katalogów artefaktów Taurus do auto-wykrywania "
            f"(domyślnie: {default_pattern})."
        ),
    )
    return parser.parse_args(args)


def main() -> int:
    args = parse_args()
    jtl_path = args.jtl or find_latest_kpi(args.artifacts_pattern)

    if not jtl_path or not jtl_path.exists():
        print("❌ Nie znaleziono pliku kpi.jtl")
        return 1

    results = defaultdict(list)
    response_times = defaultdict(list)
    errors = []
    thread_stats = defaultdict(int)

    for row in read_jtl_rows(jtl_path):
        label = str(row["label"])
        elapsed = int(row["elapsed"])
        success = bool(row["success"])
        thread = str(row["threadName"])

        results[label].append(row)
        response_times[label].append(elapsed)
        thread_stats[thread] += 1

        if not success:
            errors.append(row)

    print("=" * 80)
    print("RAPORT Z TESTÓW OBCIĄŻENIOWYCH TAURUS")
    print("=" * 80)
    print(f"Plik: {jtl_path}")
    print()

    total_requests = sum(len(r) for r in results.values())
    if total_requests == 0:
        print("Brak rekordów do analizy")
        return 1

    print(f"Całkowita liczba requestów: {total_requests}")
    print(f"Liczba błędów: {len(errors)}")
    print(
        f"Wskaźnik sukcesu: {((total_requests - len(errors)) / total_requests * 100):.2f}%"
    )
    print()

    print("=" * 80)
    print("STATYSTYKI PER ENDPOINT")
    print("=" * 80)
    print()

    for label in sorted(response_times.keys()):
        times = sorted(response_times[label])
        count = len(times)
        avg = statistics.mean(times)
        min_t = min(times)
        max_t = max(times)
        p50 = times[count // 2]
        p95 = times[min(int(count * 0.95), count - 1)]
        p99 = times[min(int(count * 0.99), count - 1)]

        print(f"\n{label}:")
        print(f"  Liczba zapytań: {count}")
        print(f"  Min: {min_t}ms")
        print(f"  Średnia: {avg:.2f}ms")
        print(f"  Mediana (P50): {p50}ms")
        print(f"  P95: {p95}ms")
        print(f"  P99: {p99}ms")
        print(f"  Max: {max_t}ms")

        successful = sum(1 for r in results[label] if r["success"])
        print(f"  Sukces: {successful}/{count} ({successful / count * 100:.2f}%)")

    print()
    print("=" * 80)
    print("STATYSTYKI WĄTKÓW")
    print("=" * 80)
    print()

    total_threads = len(thread_stats)
    print(f"Liczba unikalnych wątków: {total_threads}")
    print()

    thread_requests = sorted(thread_stats.items())
    for thread, count in thread_requests[:5]:
        print(f"  {thread}: {count} requestów")
    if len(thread_requests) > 5:
        print("  ...")

    print()
    print("=" * 80)
    print("PODSUMOWANIE")
    print("=" * 80)
    print()

    avg_all = statistics.mean(sum(response_times.values(), []))
    print(f"Średni czas odpowiedzi (ALL): {avg_all:.2f}ms")

    if avg_all < 100:
        print("✓ Wydajność: DOBRA (< 100ms)")
    elif avg_all < 500:
        print("⚠ Wydajność: AKCEPTOWALNA (< 500ms)")
    else:
        print("✗ Wydajność: SŁABA (> 500ms)")

    if len(errors) == 0:
        print("✓ Błędy: BRAK")
    else:
        print(f"✗ Błędy: {len(errors)} ({len(errors) / total_requests * 100:.2f}%)")

    print()
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
