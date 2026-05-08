"""Testy dla modułu jtl_metrics i run_pipeline."""

from pathlib import Path

import pytest

from jtl_metrics import extract_jtl_kpi, read_jtl_rows

FIXTURE_JTL = Path(__file__).parent / "fixtures" / "sample.jtl"


def test_fixture_exists():
    assert FIXTURE_JTL.exists(), f"Brak pliku fixture: {FIXTURE_JTL}"


def test_read_jtl_rows_returns_list():
    rows = read_jtl_rows(FIXTURE_JTL)
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_read_jtl_rows_fields():
    rows = read_jtl_rows(FIXTURE_JTL)
    first = rows[0]
    assert "label" in first
    assert "elapsed" in first
    assert "success" in first
    assert "responseCode" in first


def test_extract_jtl_kpi_structure():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    expected_keys = {"count", "failures", "successes", "avg_time", "min_time", "max_time",
                     "p50", "p90", "p95", "p99"}
    assert expected_keys.issubset(kpi.keys())


def test_extract_jtl_kpi_counts():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["count"] == 10
    assert kpi["failures"] == 0
    assert kpi["successes"] == 10


def test_extract_jtl_kpi_times():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["min_time"] > 0
    assert kpi["max_time"] >= kpi["min_time"]
    assert kpi["avg_time"] > 0


def test_extract_jtl_kpi_percentiles():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["p50"] > 0
    assert kpi["p90"] >= kpi["p50"]
    assert kpi["p99"] >= kpi["p90"]


def test_extract_jtl_kpi_nonexistent_file(tmp_path):
    missing = tmp_path / "nonexistent.jtl"
    kpi = extract_jtl_kpi(missing)
    assert kpi is None


def test_extract_jtl_kpi_empty_file(tmp_path):
    empty_jtl = tmp_path / "empty.jtl"
    empty_jtl.write_text("timeStamp,elapsed,label,responseCode,responseMessage,"
                         "threadName,dataType,success,failureMessage,bytes\n")
    kpi = extract_jtl_kpi(empty_jtl)
    assert kpi is not None
    assert kpi["count"] == 0
