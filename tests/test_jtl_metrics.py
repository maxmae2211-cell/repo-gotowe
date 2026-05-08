"""Testy jednostkowe dla modułu jtl_metrics."""

from pathlib import Path

import pytest

from jtl_metrics import extract_jtl_kpi, read_jtl_rows

FIXTURE_JTL = Path(__file__).parent / "fixtures" / "sample.jtl"


def test_read_jtl_rows_count():
    rows = read_jtl_rows(FIXTURE_JTL)
    assert len(rows) == 10


def test_read_jtl_rows_fields():
    rows = read_jtl_rows(FIXTURE_JTL)
    row = rows[0]
    assert "label" in row
    assert "elapsed" in row
    assert "responseCode" in row
    assert "success" in row
    assert "threadName" in row


def test_read_jtl_rows_success_type():
    rows = read_jtl_rows(FIXTURE_JTL)
    for row in rows:
        assert isinstance(row["success"], bool)
        assert isinstance(row["elapsed"], int)


def test_extract_jtl_kpi_basic():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi is not None
    assert kpi["count"] == 10
    assert kpi["failures"] == 1
    assert kpi["successes"] == 9


def test_extract_jtl_kpi_times():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["min_time"] == 75
    assert kpi["max_time"] == 300
    assert kpi["avg_time"] == pytest.approx(140.5, rel=1e-3)


def test_extract_jtl_kpi_percentiles():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["p50"] <= kpi["p90"] <= kpi["p95"] <= kpi["p99"]


def test_extract_jtl_kpi_missing_file(tmp_path):
    result = extract_jtl_kpi(tmp_path / "nonexistent.jtl")
    assert result is None


def test_extract_jtl_kpi_empty_file(tmp_path):
    empty = tmp_path / "empty.jtl"
    empty.write_text("timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success\n")
    kpi = extract_jtl_kpi(empty)
    assert kpi is not None
    assert kpi["count"] == 0
