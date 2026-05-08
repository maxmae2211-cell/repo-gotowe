"""Testy jednostkowe dla jtl_metrics.py"""
import pytest
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from jtl_metrics import extract_jtl_kpi, read_jtl_rows

SAMPLE_JTL = Path(__file__).parent / "fixtures" / "sample.jtl"


def test_read_jtl_rows_returns_list():
    rows = read_jtl_rows(SAMPLE_JTL)
    assert isinstance(rows, list)
    assert len(rows) == 10


def test_read_jtl_rows_fields():
    rows = read_jtl_rows(SAMPLE_JTL)
    row = rows[0]
    assert "label" in row
    assert "elapsed" in row
    assert "success" in row
    assert "threadName" in row


def test_extract_jtl_kpi_returns_dict():
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi is not None
    assert kpi["count"] == 10
    assert kpi["failures"] == 0
    assert kpi["successes"] == 10


def test_extract_jtl_kpi_times():
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi["min_time"] > 0
    assert kpi["max_time"] >= kpi["min_time"]
    assert kpi["avg_time"] > 0
    assert kpi["p50"] > 0
    assert kpi["p90"] >= kpi["p50"]


def test_extract_jtl_kpi_nonexistent():
    kpi = extract_jtl_kpi(Path("/nonexistent/path/kpi.jtl"))
    assert kpi is None


def test_extract_jtl_kpi_empty(tmp_path):
    empty_jtl = tmp_path / "empty.jtl"
    empty_jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,"
        "threadName,dataType,success,failureMessage,bytes,sentBytes,"
        "grpThreads,allThreads,URL,Latency,IdleTime,Connect\n"
    )
    kpi = extract_jtl_kpi(empty_jtl)
    assert kpi is not None
    assert kpi["count"] == 0
    assert kpi["failures"] == 0
