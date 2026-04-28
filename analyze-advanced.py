#!/usr/bin/env python
import csv
from pathlib import Path
from datetime import datetime

# Znajdź artefakty
artifact_dirs = sorted(Path(".").glob("2026-02-12_*"))
if not artifact_dirs:
    print("❌ Brak artifact directories")
    exit(1)

# Ostatni dir
latest = artifact_dirs[-1]
kpi_file = latest / "kpi.jtl"

print("=" * 80)
print("✅ TEST-ADVANCED.YML (ZWIĘKSZONE OBCIĄŻENIE)")
print("=" * 80)
print(f"📁 Artefakty: {latest.name}")
print(f"📅 Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if not kpi_file.exists():
    print(f"❌ {kpi_file} nie znaleziony")
    exit(1)

# Analiza KPI
elapsed_times = []
response_codes = {}
labels = {}
count = 0
failures = 0

with open(kpi_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        count += 1

        # Czasy
        try:
            elapsed = int(row.get("elapsed", 0))
            elapsed_times.append(elapsed)
        except (ValueError, TypeError):
            pass

        # Kody odpowiedzi
        code = row.get("responseCode", "UNKNOWN")
        response_codes[code] = response_codes.get(code, 0) + 1

        # Labele
        label = row.get("label", "UNKNOWN")
        labels[label] = labels.get(label, 0) + 1

        # Błędy
        if row.get("success", "").lower() != "true":
            failures += 1

if elapsed_times:
    elapsed_times.sort()
    avg = sum(elapsed_times) / len(elapsed_times)
    min_t = min(elapsed_times)
    max_t = max(elapsed_times)
    n = len(elapsed_times)

    # Percentyle
    p50_idx = int(n * 0.5)
    p90_idx = int(n * 0.9)
    p95_idx = int(n * 0.95)
    p99_idx = int(n * 0.99)

    p50 = elapsed_times[p50_idx] if p50_idx < n else elapsed_times[-1]
    p90 = elapsed_times[p90_idx] if p90_idx < n else elapsed_times[-1]
    p95 = elapsed_times[p95_idx] if p95_idx < n else elapsed_times[-1]
    p99 = elapsed_times[p99_idx] if p99_idx < n else elapsed_times[-1]

    print("📊 STATYSTYKI GŁÓWNE:")
    print("-" * 80)
    print(f"  Liczba żądań:              {count:,}")
    print(
        f"  Błędy:                     {failures} ({100*failures/count if count > 0 else 0:.2f}%)"
    )
    print(
        f"  Sukcesy:                   {count - failures} ({100*(count-failures)/count if count > 0 else 0:.2f}%)"
    )

    print("\n⏱️  CZASY ODPOWIEDZI (ms):")
    print("-" * 80)
    print(f"  Średni (AVG):              {avg:.2f} ms")
    print(f"  Minimum:                   {min_t} ms")
    print(f"  Maximum:                   {max_t} ms")
    print(f"  P50 (Mediana):             {p50} ms")
    print(f"  P90:                       {p90} ms")
    print(f"  P95:                       {p95} ms")
    print(f"  P99:                       {p99} ms")

    print("\n🔤 KODY ODPOWIEDZI:")
    print("-" * 80)
    for code in sorted(response_codes.keys()):
        count_code = response_codes[code]
        pct = 100 * count_code / count
        status = (
            "✅" if code.startswith("2") else "⚠️ " if code.startswith("3") else "❌"
        )
        print(f"  {status} {code}: {count_code:,} ({pct:.2f}%)")

    print("\n📋 SCENARIUSZE (LABELE):")
    print("-" * 80)
    for label in sorted(labels.keys()):
        count_label = labels[label]
        pct = 100 * count_label / count
        print(f"  • {label}: {count_label:,} ({pct:.2f}%)")

print("\n📈 PORÓWNANIE Z POPRZEDNIĄ WERSJĄ:")
print("-" * 80)
print("Test-Advanced (poprzednio - 10 użytkowników, 2 minuty):")
print("  Żądań: 3,235 | Średni czas: 54 ms | P50: 48 ms | P90: 85 ms")
print(f"\nTest-Advanced (teraz - 50 użytkowników, 5 minut):")
print(f"  Żądań: {count:,} | Średni czas: {avg:.2f} ms | P50: {p50} ms | P90: {p90} ms")
print(f"\n📊 Wzrost żądań: {count / 3235:.1f}× | Wzrost czasu: {avg / 54:.2f}×")

print("\n" + "=" * 80)
print("✅ ANALIZA ZAKOŃCZONA")
print("=" * 80)
