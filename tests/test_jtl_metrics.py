"""
Testy jednostkowe dla jtl_metrics.py — odczyt i agregacja metryk JTL.
Używa tests/fixtures/sample.jtl jako syntetycznej fixtury.
"""
import sys
import os
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from jtl_metrics import extract_jtl_kpi, read_jtl_rows  # noqa: E402

FIXTURE_JTL = Path(__file__).parent / "fixtures" / "sample.jtl"
EXPECTED_SAMPLE_COUNT = 10


def test_fixture_exists():
    assert FIXTURE_JTL.exists(), f"Brak fixtury: {FIXTURE_JTL}"


def test_read_jtl_rows_count():
    rows = read_jtl_rows(FIXTURE_JTL)
    assert len(rows) == EXPECTED_SAMPLE_COUNT


def test_read_jtl_rows_fields():
    rows = read_jtl_rows(FIXTURE_JTL)
    for row in rows:
        assert "label" in row
        assert "elapsed" in row
        assert "responseCode" in row
        assert "success" in row
        assert "threadName" in row


def test_read_jtl_rows_all_success():
    rows = read_jtl_rows(FIXTURE_JTL)
    assert all(row["success"] is True for row in rows)


def test_extract_jtl_kpi_count():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    assert kpi["count"] == EXPECTED_SAMPLE_COUNT


def test_extract_jtl_kpi_no_failures():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    assert kpi["failures"] == 0
    assert kpi["successes"] == EXPECTED_SAMPLE_COUNT


def test_extract_jtl_kpi_avg_time():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    # Średni czas odpowiedzi powinien być < 200 ms
    assert kpi["avg_time"] < 200
    assert kpi["avg_time"] > 0


def test_extract_jtl_kpi_min_max():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    assert kpi["min_time"] <= kpi["avg_time"]
    assert kpi["max_time"] >= kpi["avg_time"]


def test_extract_jtl_kpi_percentiles():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    assert kpi["p50"] <= kpi["p90"]
    assert kpi["p90"] <= kpi["p95"]
    assert kpi["p95"] <= kpi["p99"]


def test_extract_jtl_kpi_missing_file():
    result = extract_jtl_kpi(Path("nonexistent.jtl"))
    assert result is None


def test_extract_jtl_kpi_times_sorted():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    times = kpi["times"]
    assert times == sorted(times)
