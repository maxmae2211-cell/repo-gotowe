"""Testy jednostkowe dla modułu jtl_metrics."""

from pathlib import Path

import pytest

from jtl_metrics import extract_jtl_kpi, read_jtl_rows

FIXTURE_JTL = Path(__file__).parent / "fixtures" / "sample.jtl"

_JTL_HEADER = (
    "timeStamp,elapsed,label,responseCode,responseMessage,threadName,"
    "dataType,success,failureMessage,bytes,sentBytes,grpThreads,allThreads,"
    "URL,Latency,IdleTime,Connect\n"
)


# ---------------------------------------------------------------------------
# read_jtl_rows
# ---------------------------------------------------------------------------

def test_read_jtl_rows_returns_list():
    rows = read_jtl_rows(FIXTURE_JTL)
    assert isinstance(rows, list)
    assert len(rows) == 10


def test_read_jtl_rows_fields():
    rows = read_jtl_rows(FIXTURE_JTL)
    for row in rows:
        assert "label" in row
        assert "elapsed" in row
        assert "responseCode" in row
        assert "success" in row
        assert "threadName" in row


def test_read_jtl_rows_success_is_bool():
    rows = read_jtl_rows(FIXTURE_JTL)
    for row in rows:
        assert isinstance(row["success"], bool)


def test_read_jtl_rows_elapsed_is_int():
    rows = read_jtl_rows(FIXTURE_JTL)
    for row in rows:
        assert isinstance(row["elapsed"], int)


def test_read_jtl_rows_empty_file(tmp_path):
    empty = tmp_path / "empty.jtl"
    empty.write_text(_JTL_HEADER)
    rows = read_jtl_rows(empty)
    assert rows == []


# ---------------------------------------------------------------------------
# extract_jtl_kpi
# ---------------------------------------------------------------------------

def test_extract_jtl_kpi_returns_dict():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert isinstance(kpi, dict)


def test_extract_jtl_kpi_count():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["count"] == 10


def test_extract_jtl_kpi_no_failures():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["failures"] == 0
    assert kpi["successes"] == 10


def test_extract_jtl_kpi_avg_time_under_threshold():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["avg_time"] < 200


def test_extract_jtl_kpi_times_ordered():
    kpi = extract_jtl_kpi(FIXTURE_JTL)
    assert kpi["min_time"] <= kpi["p50"] <= kpi["p90"] <= kpi["p95"] <= kpi["p99"] <= kpi["max_time"]


def test_extract_jtl_kpi_nonexistent_file():
    result = extract_jtl_kpi(Path("nonexistent_path/file.jtl"))
    assert result is None


def test_extract_jtl_kpi_with_failures(tmp_path):
    jtl = tmp_path / "failures.jtl"
    jtl.write_text(
        _JTL_HEADER
        + "1000000,100,Test,200,OK,t1,text,true,,100,50,1,1,http://x,90,0,10\n"
        + "1000100,150,Test,500,Error,t1,text,false,Error,100,50,1,1,http://x,140,0,10\n"
    )
    kpi = extract_jtl_kpi(jtl)
    assert kpi["count"] == 2
    assert kpi["failures"] == 1
    assert kpi["successes"] == 1


def test_extract_jtl_kpi_empty_file(tmp_path):
    jtl = tmp_path / "empty.jtl"
    jtl.write_text(_JTL_HEADER)
    kpi = extract_jtl_kpi(jtl)
    assert kpi["count"] == 0
    assert kpi["failures"] == 0
