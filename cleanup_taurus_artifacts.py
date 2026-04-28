#!/usr/bin/env python3
"""
Usuwa katalogi artefaktów Taurus starsze niż 7 dni, pozostawiając 5 najnowszych.
"""
from pathlib import Path
from datetime import datetime, timedelta
import shutil

ARTIFACT_PATTERN = "2026-*"
KEEP_LATEST = 5
MAX_AGE_DAYS = 7

folders = sorted([p for p in Path(".").glob(ARTIFACT_PATTERN) if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)

now = datetime.now()
deleted = []

for folder in folders[KEEP_LATEST:]:
    mtime = datetime.fromtimestamp(folder.stat().st_mtime)
    if (now - mtime).days > MAX_AGE_DAYS:
        shutil.rmtree(folder)
        deleted.append(folder.name)

if deleted:
    print("Usunięto katalogi:")
    for name in deleted:
        print(f" - {name}")
else:
    print("Brak katalogów do usunięcia.")
