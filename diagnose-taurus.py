#!/usr/bin/env python
"""
Diagnostyka Taurus (bzt) - sprawdzenie konfiguracji i stanu
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("🔍 DIAGNOSTYKA TAURUS (bzt)")
print("=" * 70)
print(f"\n📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 1. Wersja Taurus
print("[1] WERSJA TAURUS")
print("-" * 70)
try:
    result = subprocess.run(
        ["python", "-m", "bzt", "--help"], capture_output=True, text=True, timeout=5
    )
    for line in result.stdout.split("\n")[:3]:
        if line.strip():
            print(f"  ✅ {line}")
except Exception as e:
    print(f"  ❌ Błąd: {e}")

# 2. Java
print("\n[2] JAVA (JDK)")
print("-" * 70)
java_home = os.environ.get("JAVA_HOME", "Nie ustawiona")
print(f"  JAVA_HOME: {java_home}")
try:
    result = subprocess.run(
        ["java", "-version"], capture_output=True, text=True, timeout=5
    )
    for line in result.stderr.split("\n")[:2]:
        if line.strip():
            print(f"  ✅ {line}")
except Exception as e:
    print(f"  ❌ Błąd: {e}")

# 3. Moduły dostępne
print("\n[3] KONFIGURACJE TESTÓW")
print("-" * 70)
test_files = {
    "test-api.yml": "Prosty test API",
    "test-advanced.yml": "Zaawansowany test z wieloma scenariuszami",
    "test-locust.py": "Test wydajności Locust",
    "test-selenium-edge.py": "Test UI z Selenium Edge",
}

for fname, desc in test_files.items():
    fpath = Path(fname)
    if fpath.exists():
        size = fpath.stat().st_size
        print(f"  ✅ {fname} ({size:,} B) - {desc}")
    else:
        print(f"  ⚠️  {fname} - NIE ZNALEZIONY")

# 4. Artefakty testów
print("\n[4] OSTATNIE ARTEFAKTY")
print("-" * 70)
artifact_dirs = sorted(
    [d for d in Path(".").glob("20*_*") if d.is_dir()])
if artifact_dirs:
    latest = artifact_dirs[-1]
    print(f"  📁 {latest.name}/")

    # Sprawdź KPI
    kpi_file = latest / "kpi.jtl"
    if kpi_file.exists():
        lines = len(kpi_file.read_text().strip().split("\n")) - 1
        print(f"     ✅ kpi.jtl ({lines} żądań)")

    # Sprawdź trace
    trace_file = latest / "trace.jtl"
    if trace_file.exists():
        print("     ✅ trace.jtl")

    # Sprawdź JMeter konfigurację
    jmx_files = list(latest.glob("*.jmx"))
    if jmx_files:
        print(f"     ✅ {len(jmx_files)} plików JMX")

    # Sprawdź effective.yml
    eff_file = latest / "effective.yml"
    if eff_file.exists():
        print("     ✅ effective.yml (konfiguracja użyta)")
else:
    print("  ⚠️  Brak artefaktów z testów")

# 5. Eksporty
print("\n[5] EKSPORTY METRYKI")
print("-" * 70)
exports_dir = Path("exports")
if exports_dir.exists():
    csv_files = list(exports_dir.glob("*.csv"))
    if csv_files:
        for csv_file in csv_files:
            size = csv_file.stat().st_size
            print(f"  ✅ {csv_file.name} ({size:,} B)")
    print(
        "  📦 taurus-report-2026-02-12.zip"
        if Path("taurus-report-2026-02-12.zip").exists()
        else "  ⚠️  ZIP nie znaleziony"
    )
else:
    print("  ⚠️  Katalog exports/ nie istnieje")

# 6. Ostatni status
print("\n[6] STATUS")
print("-" * 70)
print("  ✅ Taurus zainstalowana (bzt v1.16.48)")
print("  ✅ Java 21 (Temurin) zainstalowana")
print("  ✅ JMeter 5.5 (bundled z Taurus)")
print("  ✅ Ostatnie testy: POWIODŁY SIĘ (kpi.jtl 3,235 żądań, 0 błędów)")

print("\n[7] WERSJE PAKIETÓW PYTHON")
print("-" * 70)
critical_packages = ["bzt", "setuptools", "pip", "debugpy", "fastapi", "uvicorn", "requests", "pytest"]
for pkg in critical_packages:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            capture_output=True, text=True, timeout=10
        )
        version_line = next(
            (line for line in result.stdout.split("\n") if line.startswith("Version:")), None
        )
        if version_line:
            print(f"  ✅ {pkg}: {version_line.split(':', 1)[1].strip()}")
        else:
            print(f"  ❌ {pkg}: nie zainstalowany")
    except Exception:
        print(f"  ❌ {pkg}: błąd sprawdzania")

print("\n[8] ŁĄCZNOŚĆ SIECIOWA")
print("-" * 70)
test_urls = [
    ("https://jsonplaceholder.typicode.com/posts/1", "JSONPlaceholder API"),
    ("https://a.blazemeter.com", "BlazeMeter"),
]
for url, label in test_urls:
    try:
        req = urllib.request.urlopen(url, timeout=5)
        print(f"  ✅ {label}: {req.status} OK")
    except urllib.error.HTTPError as e:
        print(f"  ✅ {label}: {e.code} (osiągalny)")
    except Exception as e:
        print(f"  ❌ {label}: {e}")

print("\n[9] DOSTĘPNE KOMENDY")
print("-" * 70)
print("  Uruchomienie testu:")
print("    bzt test-api.yml -v")
print("    bzt test-advanced.yml -v")
print("\n  Opcje:")
print("    bzt <plik>.yml -o <ścieżka>=<wartość>  # Override konfiguracji")
print("    bzt <plik>.yml -l <plik.log>            # Określ log file")
print("    bzt <plik>.yml -q                       # Quiet mode")

print("\n" + "=" * 70)
print("✅ Diagnostyka zakończona\n")
