#!/usr/bin/env python3
"""
Usuwa katalogi artefaktów Taurus starsze niż 7 dni, pozostawiając 5 najnowszych.
"""

import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta
import shutil

ARTIFACT_PATTERN = "2026-*"


def get_keep_latest():
    env_val = os.getenv("KEEP_LATEST")
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            pass
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-latest",
        type=int,
        default=5,
        help="Ile najnowszych katalogów artefaktów zachować",
    )
    args, _ = parser.parse_known_args()
    return args.keep_latest


KEEP_LATEST = get_keep_latest()
MAX_AGE_DAYS = 7

folders = sorted(
    [p for p in Path(".").glob(ARTIFACT_PATTERN) if p.is_dir()],
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)

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
