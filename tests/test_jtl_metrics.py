"""Testy jednostkowe dla modułu jtl_metrics."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from jtl_metrics import extract_jtl_kpi, read_jtl_rows

SAMPLE_JTL = Path(__file__).parent / "fixtures" / "sample.jtl"


# ---------------------------------------------------------------------------
# Testy na syntetycznym fixture
# ---------------------------------------------------------------------------

def test_sample_jtl_exists():
    """Fixture sample.jtl musi istnieć."""
    assert SAMPLE_JTL.exists(), f"Brak pliku: {SAMPLE_JTL}"


def test_read_jtl_rows_count():
    """read_jtl_rows zwraca poprawną liczbę wierszy."""
    rows = read_jtl_rows(SAMPLE_JTL)
    assert len(rows) == 10


def test_read_jtl_rows_fields():
    """Każdy wiersz ma wymagane pola."""
    rows = read_jtl_rows(SAMPLE_JTL)
    required = {"label", "elapsed", "responseCode", "success", "threadName"}
    for row in rows:
        assert required.issubset(row.keys()), f"Brakujące pola w wierszu: {row}"


def test_read_jtl_rows_types():
    """Pole 'elapsed' jest int, 'success' jest bool."""
    rows = read_jtl_rows(SAMPLE_JTL)
    for row in rows:
        assert isinstance(row["elapsed"], int)
        assert isinstance(row["success"], bool)


def test_extract_jtl_kpi_count():
    """extract_jtl_kpi zlicza żądania poprawnie."""
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi is not None
    assert kpi["count"] == 10


def test_extract_jtl_kpi_no_failures():
    """Fixture nie powinien mieć błędów (wszystkie success=true)."""
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi is not None
    assert kpi["failures"] == 0
    assert kpi["successes"] == 10


def test_extract_jtl_kpi_avg_time():
    """Średni czas odpowiedzi jest dodatni."""
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi is not None
    assert kpi["avg_time"] > 0


def test_extract_jtl_kpi_times_sorted():
    """Lista czasów w KPI jest posortowana rosnąco."""
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi is not None
    times = kpi["times"]
    assert times == sorted(times)


def test_extract_jtl_kpi_percentiles():
    """Percentyle p50 <= p90 <= p95 <= p99."""
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi is not None
    assert kpi["p50"] <= kpi["p90"] <= kpi["p95"] <= kpi["p99"]


def test_extract_jtl_kpi_min_max():
    """min_time <= avg_time <= max_time."""
    kpi = extract_jtl_kpi(SAMPLE_JTL)
    assert kpi is not None
    assert kpi["min_time"] <= kpi["avg_time"] <= kpi["max_time"]


# ---------------------------------------------------------------------------
# Testy na danych syntetycznych (tmp_path)
# ---------------------------------------------------------------------------

def _write_jtl(path: Path, rows: list[dict]) -> None:
    fieldnames = ["timeStamp", "elapsed", "label", "responseCode",
                  "responseMessage", "threadName", "dataType", "success",
                  "failureMessage", "bytes", "sentBytes", "grpThreads",
                  "allThreads", "URL", "Latency", "IdleTime", "Connect"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _make_row(elapsed: int = 100, success: str = "true",
              label: str = "GET /test") -> dict:
    return {
        "timeStamp": "1746100000000",
        "elapsed": str(elapsed),
        "label": label,
        "responseCode": "200",
        "responseMessage": "OK",
        "threadName": "Thread Group 1-1",
        "dataType": "text",
        "success": success,
        "failureMessage": "",
        "bytes": "1024",
        "sentBytes": "256",
        "grpThreads": "1",
        "allThreads": "1",
        "URL": "https://jsonplaceholder.typicode.com/test",
        "Latency": "90",
        "IdleTime": "0",
        "Connect": "8",
    }


def test_extract_jtl_kpi_missing_file(tmp_path):
    """extract_jtl_kpi zwraca None dla nieistniejącego pliku."""
    result = extract_jtl_kpi(tmp_path / "nonexistent.jtl")
    assert result is None


def test_extract_jtl_kpi_empty_file(tmp_path):
    """extract_jtl_kpi zwraca pusty KPI dla pliku bez danych."""
    empty = tmp_path / "empty.jtl"
    _write_jtl(empty, [])
    kpi = extract_jtl_kpi(empty)
    assert kpi is not None
    assert kpi["count"] == 0
    assert kpi["failures"] == 0


def test_extract_jtl_kpi_with_failures(tmp_path):
    """extract_jtl_kpi poprawnie liczy błędy."""
    jtl = tmp_path / "failures.jtl"
    rows = [
        _make_row(100, "true"),
        _make_row(200, "false"),
        _make_row(150, "false"),
    ]
    _write_jtl(jtl, rows)
    kpi = extract_jtl_kpi(jtl)
    assert kpi is not None
    assert kpi["count"] == 3
    assert kpi["failures"] == 2
    assert kpi["successes"] == 1


def test_extract_jtl_kpi_single_row(tmp_path):
    """extract_jtl_kpi działa dla jednego wiersza."""
    jtl = tmp_path / "single.jtl"
    _write_jtl(jtl, [_make_row(123)])
    kpi = extract_jtl_kpi(jtl)
    assert kpi is not None
    assert kpi["count"] == 1
    assert kpi["avg_time"] == 123.0
    assert kpi["min_time"] == kpi["max_time"] == 123


def test_read_jtl_rows_success_false(tmp_path):
    """read_jtl_rows parsuje success=false jako False."""
    jtl = tmp_path / "fail.jtl"
    _write_jtl(jtl, [_make_row(100, "false")])
    rows = read_jtl_rows(jtl)
    assert rows[0]["success"] is False


def test_read_jtl_rows_success_true(tmp_path):
    """read_jtl_rows parsuje success=true jako True."""
    jtl = tmp_path / "ok.jtl"
    _write_jtl(jtl, [_make_row(100, "true")])
    rows = read_jtl_rows(jtl)
    assert rows[0]["success"] is True
