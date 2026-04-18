#!/usr/bin/env python
import csv
from pathlib import Path
from statistics import median, quantiles

jtl_file = Path("2026-02-12_03-45-44.209512/kpi.jtl")

if not jtl_file.exists():
    print("❌ kpi.jtl not found")
    exit(1)

elapsed_times = []
count = 0
failures = 0

with open(jtl_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        count += 1
        try:
            elapsed = int(row.get('elapsed', 0))
            elapsed_times.append(elapsed)
            if row.get('success', '').lower() != 'true':
                failures += 1
        except ValueError:
            pass

if elapsed_times:
    elapsed_times.sort()
    avg = sum(elapsed_times) / len(elapsed_times)
    min_t = min(elapsed_times)
    max_t = max(elapsed_times)
    p50 = median(elapsed_times)
    
    # Calculate percentiles
    n = len(elapsed_times)
    p90_idx = int(n * 0.9)
    p95_idx = int(n * 0.95)
    p99_idx = int(n * 0.99) if n > 100 else n - 1
    
    p90 = elapsed_times[p90_idx] if p90_idx < n else elapsed_times[-1]
    p95 = elapsed_times[p95_idx] if p95_idx < n else elapsed_times[-1]
    p99 = elapsed_times[p99_idx] if p99_idx < n else elapsed_times[-1]
    
    print("=" * 70)
    print("✅ TEST-API.YML (ZWIĘKSZONE OBCIĄŻENIE)")
    print("=" * 70)
    print(f"Liczba żądań:         {count}")
    print(f"Błędy:                {failures}")
    print(f"Sukcesy:              {count - failures}")
    print(f"\nCzasy odpowiedzi (ms):")
    print(f"  Średni (AVG):       {avg:.2f} ms")
    print(f"  Minimum:            {min_t} ms")
    print(f"  Maximum:            {max_t} ms")
    print(f"  P50 (Mediana):      {p50} ms")
    print(f"  P90:                {p90} ms")
    print(f"  P95:                {p95} ms")
    print(f"  P99:                {p99} ms")
    print("=" * 70)
    
    print("\n📊 PORÓWNANIE WYNIKÓW:")
    print("-" * 70)
    print("Test API (poprzednio):")
    print("  Żądań: 92, Średni czas: 99 ms, P50: 134 ms")
    print("\nTest API (z nowym obciążeniem):")
    print(f"  Żądań: {count}, Średni czas: {avg:.2f} ms, P50: {p50} ms")
    print("-" * 70)
else:
    print("❌ No timing data found")
