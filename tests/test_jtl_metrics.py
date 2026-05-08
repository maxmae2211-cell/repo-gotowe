"""Testy dla jtl_metrics.py – odczyt i agregacja metryk JTL."""
import sys
import os
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from jtl_metrics import read_jtl_rows, extract_jtl_kpi

FIXTURE = Path(__file__).parent / "fixtures" / "sample.jtl"


# ---------------------------------------------------------------------------
# read_jtl_rows
# ---------------------------------------------------------------------------

def test_read_jtl_rows_returns_list():
    rows = read_jtl_rows(FIXTURE)
    assert isinstance(rows, list)
    assert len(rows) == 10


def test_read_jtl_rows_keys():
    rows = read_jtl_rows(FIXTURE)
    for row in rows:
        assert "label" in row
        assert "elapsed" in row
        assert "success" in row
        assert "responseCode" in row
        assert "threadName" in row


def test_read_jtl_rows_success_type():
    rows = read_jtl_rows(FIXTURE)
    for row in rows:
        assert isinstance(row["success"], bool)


def test_read_jtl_rows_elapsed_type():
    rows = read_jtl_rows(FIXTURE)
    for row in rows:
        assert isinstance(row["elapsed"], int)
        assert row["elapsed"] > 0


# ---------------------------------------------------------------------------
# extract_jtl_kpi
# ---------------------------------------------------------------------------

def test_extract_jtl_kpi_count():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi is not None
    assert kpi["count"] == 10


def test_extract_jtl_kpi_no_failures():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["failures"] == 0
    assert kpi["successes"] == 10


def test_extract_jtl_kpi_avg_time_range():
    kpi = extract_jtl_kpi(FIXTURE)
    assert 50 < kpi["avg_time"] < 300


def test_extract_jtl_kpi_min_max():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["min_time"] <= kpi["avg_time"]
    assert kpi["avg_time"] <= kpi["max_time"]


def test_extract_jtl_kpi_percentiles_ordered():
    kpi = extract_jtl_kpi(FIXTURE)
    assert kpi["p50"] <= kpi["p90"]
    assert kpi["p90"] <= kpi["p95"]
    assert kpi["p95"] <= kpi["p99"]


def test_extract_jtl_kpi_missing_file():
    result = extract_jtl_kpi(Path("/nonexistent/path/kpi.jtl"))
    assert result is None


def test_extract_jtl_kpi_empty_file(tmp_path):
    empty_jtl = tmp_path / "empty.jtl"
    empty_jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,"
        "threadName,dataType,success,failureMessage,bytes,sentBytes,"
        "grpThreads,allThreads,URL,Filename,Latency,Connect\n"
    )
    kpi = extract_jtl_kpi(empty_jtl)
    assert kpi is not None
    assert kpi["count"] == 0
    assert kpi["failures"] == 0


def test_extract_jtl_kpi_with_failures(tmp_path):
    jtl_path = tmp_path / "kpi.jtl"
    jtl_path.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,"
        "threadName,dataType,success,failureMessage,bytes,sentBytes,"
        "grpThreads,allThreads,URL,Filename,Latency,Connect\n"
        "1000,100,GET /ok,200,OK,T-1,text,true,,100,10,1,1,http://x,,99,5\n"
        "1100,200,GET /err,500,Error,T-1,text,false,Failed,50,10,1,1,http://x,,199,5\n"
    )
    kpi = extract_jtl_kpi(jtl_path)
    assert kpi["count"] == 2
    assert kpi["failures"] == 1
    assert kpi["successes"] == 1
