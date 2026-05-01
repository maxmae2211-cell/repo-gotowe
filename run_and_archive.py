"""
run_and_archive.py — uruchamiany po każdym commit (post-commit hook).
Archiwizuje wyniki testów Taurus i regeneruje raport HTML.
"""
import subprocess
import sys
import zipfile
import os
from datetime import datetime
from pathlib import Path


def archive_taurus_results():
    """Zipuje najnowszy katalog wyników Taurus."""
    root = Path(__file__).parent
    dirs = sorted(root.glob("20??-??-??_??-??-??.??????"))
    if not dirs:
        return None
    latest = dirs[-1]
    archive_name = root / f"taurus-report-{latest.name}.zip"
    if archive_name.exists():
        return str(archive_name)
    with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in latest.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(root))
    print(f"📦 Zarchiwizowano: {archive_name.name}")
    return str(archive_name)


def regenerate_report():
    """Regeneruje raport HTML."""
    result = subprocess.run(
        [sys.executable, "generate_report.py",
            "--output", "taurus-locust-report.html"],
        capture_output=True, text=True, cwd=Path(__file__).parent
    )
    if result.returncode == 0:
        print("📊 Raport HTML zaktualizowany")
    else:
        print(f"⚠️  Raport: {result.stderr.strip()}", file=sys.stderr)


if __name__ == "__main__":
    print(f"🔄 post-commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    archive_taurus_results()
    regenerate_report()
