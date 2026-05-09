"""Testy jednostkowe dla modułu jtl_metrics."""
import pytest
from pathlib import Path

from jtl_metrics import extract_jtl_kpi, read_jtl_rows

FIXTURE = Path(__file__).parent / "fixtures" / "sample.jtl"


def test_fixture_exists():
    assert FIXTURE.exists(), f"Plik fixture nie istnieje: {FIXTURE}"


def test_read_jtl_rows_count():
    rows = read_jtl_rows(FIXTURE)
    assert len(rows) == 10


def test_read_jtl_rows_fields():
    rows = read_jtl_rows(FIXTURE)
    for row in rows:
        assert "label" in row
        assert "elapsed" in row
        assert "success" in row


def test_extract_jtl_kpi_count():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi is not None
    assert kpi["count"] == 10


def test_extract_jtl_kpi_no_failures():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["failures"] == 0
    assert kpi["successes"] == 10


def test_extract_jtl_kpi_times():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["min_time"] == 78
    assert kpi["max_time"] == 160
    assert 100 <= kpi["avg_time"] <= 130


def test_extract_jtl_kpi_percentiles():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["p50"] > 0
    assert kpi["p90"] >= kpi["p50"]
    assert kpi["p99"] >= kpi["p90"]


def test_extract_jtl_kpi_missing_file(tmp_path):
    result = extract_jtl_kpi(tmp_path / "nonexistent.jtl")
    assert result is None


def test_extract_jtl_kpi_empty_file(tmp_path):
    empty = tmp_path / "empty.jtl"
    empty.write_text("timeStamp,elapsed,label,responseCode,success\n")
    result = extract_jtl_kpi(empty)
    assert result is not None
    assert result["count"] == 0
