"""Unit tests for jtl_metrics.py"""
from pathlib import Path

import pytest

from jtl_metrics import extract_jtl_kpi, read_jtl_rows

FIXTURE = Path(__file__).parent / "fixtures" / "sample.jtl"


# ---------------------------------------------------------------------------
# read_jtl_rows
# ---------------------------------------------------------------------------

def test_read_jtl_rows_count():
    rows = read_jtl_rows(FIXTURE)
    assert len(rows) == 10


def test_read_jtl_rows_fields():
    rows = read_jtl_rows(FIXTURE)
    row = rows[0]
    assert "label" in row
    assert "elapsed" in row
    assert "success" in row
    assert "threadName" in row


def test_read_jtl_rows_success_type():
    rows = read_jtl_rows(FIXTURE)
    for row in rows:
        assert isinstance(row["success"], bool)


def test_read_jtl_rows_elapsed_type():
    rows = read_jtl_rows(FIXTURE)
    for row in rows:
        assert isinstance(row["elapsed"], int)


# ---------------------------------------------------------------------------
# extract_jtl_kpi — fixture file
# ---------------------------------------------------------------------------

def test_extract_kpi_count():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi is not None
    assert kpi["count"] == 10


def test_extract_kpi_no_failures():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["failures"] == 0
    assert kpi["successes"] == 10


def test_extract_kpi_avg_time():
    kpi = extract_jtl_kpi(FIXTURE)
    # times: 78,95,110,120,100,105,90,115,88,160 -> avg = 106.1
    assert abs(kpi["avg_time"] - 106.1) < 0.01


def test_extract_kpi_min_max():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["min_time"] == 78
    assert kpi["max_time"] == 160


def test_extract_kpi_percentiles():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["p50"] > 0
    assert kpi["p90"] >= kpi["p50"]
    assert kpi["p99"] >= kpi["p90"]


# ---------------------------------------------------------------------------
# extract_jtl_kpi — edge cases
# ---------------------------------------------------------------------------

def test_extract_kpi_missing_file():
    result = extract_jtl_kpi(Path("/nonexistent/path/kpi.jtl"))
    assert result is None


def test_extract_kpi_empty_file(tmp_path):
    empty = tmp_path / "empty.jtl"
    empty.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,"
        "threadName,dataType,success,failureMessage\n"
    )
    kpi = extract_jtl_kpi(empty)
    assert kpi is not None
    assert kpi["count"] == 0
    assert kpi["failures"] == 0


def test_extract_kpi_with_failures(tmp_path):
    jtl = tmp_path / "fail.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage\n"
        "1715000000000,200,GET /api,200,OK,Thread 1-1,text,true,\n"
        "1715000000300,500,GET /api,500,Error,Thread 1-1,text,false,Connection refused\n"
    )
    kpi = extract_jtl_kpi(jtl)
    assert kpi["count"] == 2
    assert kpi["failures"] == 1
    assert kpi["successes"] == 1
