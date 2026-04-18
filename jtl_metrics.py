#!/usr/bin/env python3
"""Wspólne funkcje do odczytu i agregacji metryk z plików JTL."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _percentile(sorted_values: List[int], pct: float) -> int:
    if not sorted_values:
        return 0
    index = int(len(sorted_values) * pct)
    if index >= len(sorted_values):
        index = len(sorted_values) - 1
    return sorted_values[index]


def read_jtl_rows(jtl_path: Path) -> List[Dict[str, object]]:
    """Zwraca rekordy JTL ze znormalizowanymi polami potrzebnymi do analiz."""
    rows: List[Dict[str, object]] = []

    with jtl_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "label": row.get("label", "unknown"),
                    "elapsed": _to_int(row.get("elapsed", 0), 0),
                    "responseCode": row.get("responseCode", ""),
                    "success": str(row.get("success", "")).lower() == "true",
                    "threadName": row.get("threadName", ""),
                }
            )

    return rows


def extract_jtl_kpi(jtl_path: Path) -> Optional[Dict[str, object]]:
    """Agreguje podstawowe metryki KPI dla jednego pliku JTL."""
    if not jtl_path.exists():
        return None

    rows = read_jtl_rows(jtl_path)
    if not rows:
        return {
            "count": 0,
            "failures": 0,
            "successes": 0,
            "avg_time": 0,
            "min_time": 0,
            "max_time": 0,
            "p50": 0,
            "p90": 0,
            "p95": 0,
            "p99": 0,
            "times": [],
        }

    times = [int(row["elapsed"]) for row in rows]
    times.sort()

    count = len(rows)
    failures = sum(1 for row in rows if not bool(row["success"]))
    successes = count - failures

    return {
        "count": count,
        "failures": failures,
        "successes": successes,
        "avg_time": sum(times) / count,
        "min_time": times[0],
        "max_time": times[-1],
        "p50": _percentile(times, 0.50),
        "p90": _percentile(times, 0.90),
        "p95": _percentile(times, 0.95),
        "p99": _percentile(times, 0.99),
        "times": times,
        "rows": rows,
    }


def find_latest_kpi(pattern: str) -> Optional[Path]:
    """Zwraca ścieżkę do najnowszego pliku kpi.jtl pasującego do wzorca katalogów."""
    default_pattern = f"{datetime.now().year}-*"
    candidates = sorted(Path(".").glob(pattern or default_pattern), reverse=True)
    for directory in candidates:
        if directory.is_dir():
            jtl_file = directory / "kpi.jtl"
            if jtl_file.exists():
                return jtl_file
    return None
