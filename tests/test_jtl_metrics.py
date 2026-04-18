"""Unit tests for jtl_metrics shared library."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

# Ensure project root is importable regardless of working directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from jtl_metrics import _percentile, _to_int, extract_jtl_kpi, find_latest_kpi, read_jtl_rows

FIXTURE_JTL = Path(__file__).parent / "fixtures" / "sample.jtl"


# ---------------------------------------------------------------------------
# _to_int
# ---------------------------------------------------------------------------

class TestToInt:
    def test_valid_int_string(self):
        assert _to_int("42") == 42

    def test_valid_int(self):
        assert _to_int(7) == 7

    def test_none_returns_default(self):
        assert _to_int(None, default=0) == 0

    def test_non_numeric_string_returns_default(self):
        assert _to_int("abc", default=-1) == -1

    def test_empty_string_returns_default(self):
        assert _to_int("", default=5) == 5


# ---------------------------------------------------------------------------
# _percentile
# ---------------------------------------------------------------------------

class TestPercentile:
    def test_empty_list_returns_zero(self):
        assert _percentile([], 0.50) == 0

    def test_p50_on_single_element(self):
        assert _percentile([100], 0.50) == 100

    def test_p50_on_even_list(self):
        values = [10, 20, 30, 40]
        # index = int(4 * 0.5) = 2  → values[2] = 30
        assert _percentile(values, 0.50) == 30

    def test_p99_clamps_to_last_element(self):
        values = [1, 2, 3]
        # index = int(3 * 0.99) = 2  → values[2] = 3
        assert _percentile(values, 0.99) == 3

    def test_p0_returns_first(self):
        assert _percentile([5, 10, 15], 0.0) == 5

    def test_p100_returns_last(self):
        # index = int(3 * 1.0) = 3 → clamped to 2 → values[2] = 15
        assert _percentile([5, 10, 15], 1.0) == 15


# ---------------------------------------------------------------------------
# read_jtl_rows
# ---------------------------------------------------------------------------

class TestReadJtlRows:
    def test_reads_fixture(self):
        rows = read_jtl_rows(FIXTURE_JTL)
        assert len(rows) == 10

    def test_row_fields_present(self):
        rows = read_jtl_rows(FIXTURE_JTL)
        row = rows[0]
        assert "label" in row
        assert "elapsed" in row
        assert "success" in row
        assert "threadName" in row
        assert "responseCode" in row

    def test_success_is_bool(self):
        rows = read_jtl_rows(FIXTURE_JTL)
        for row in rows:
            assert isinstance(row["success"], bool)

    def test_elapsed_is_int(self):
        rows = read_jtl_rows(FIXTURE_JTL)
        for row in rows:
            assert isinstance(row["elapsed"], int)

    def test_failed_row_detected(self):
        rows = read_jtl_rows(FIXTURE_JTL)
        failed = [r for r in rows if not r["success"]]
        assert len(failed) == 1
        assert failed[0]["responseCode"] == "500"

    def test_empty_jtl(self, tmp_path):
        empty_jtl = tmp_path / "empty.jtl"
        empty_jtl.write_text(
            "timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success\n",
            encoding="utf-8",
        )
        rows = read_jtl_rows(empty_jtl)
        assert rows == []


# ---------------------------------------------------------------------------
# extract_jtl_kpi
# ---------------------------------------------------------------------------

class TestExtractJtlKpi:
    def test_returns_none_for_nonexistent_file(self, tmp_path):
        assert extract_jtl_kpi(tmp_path / "missing.jtl") is None

    def test_returns_zero_kpi_for_empty_file(self, tmp_path):
        empty_jtl = tmp_path / "empty.jtl"
        empty_jtl.write_text(
            "timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success\n",
            encoding="utf-8",
        )
        kpi = extract_jtl_kpi(empty_jtl)
        assert kpi is not None
        assert kpi["count"] == 0

    def test_fixture_kpi_counts(self):
        kpi = extract_jtl_kpi(FIXTURE_JTL)
        assert kpi is not None
        assert kpi["count"] == 10
        assert kpi["failures"] == 1
        assert kpi["successes"] == 9

    def test_fixture_kpi_times(self):
        kpi = extract_jtl_kpi(FIXTURE_JTL)
        assert kpi["min_time"] == 75
        assert kpi["max_time"] == 500

    def test_fixture_avg_time(self):
        kpi = extract_jtl_kpi(FIXTURE_JTL)
        # elapsed values: 120,85,200,95,310,75,500,110,180,90  → sum=1765, avg=176.5
        assert abs(kpi["avg_time"] - 176.5) < 0.01

    def test_fixture_percentiles_ordered(self):
        kpi = extract_jtl_kpi(FIXTURE_JTL)
        assert kpi["p50"] <= kpi["p90"] <= kpi["p95"] <= kpi["p99"]

    def test_kpi_has_all_keys(self):
        kpi = extract_jtl_kpi(FIXTURE_JTL)
        for key in ("count", "failures", "successes", "avg_time", "min_time",
                    "max_time", "p50", "p90", "p95", "p99", "times", "rows"):
            assert key in kpi, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# find_latest_kpi
# ---------------------------------------------------------------------------

class TestFindLatestKpi:
    def test_returns_none_when_no_match(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert find_latest_kpi("nonexistent-*") is None

    def test_finds_jtl_in_matching_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        artifact_dir = tmp_path / "2026-01-01_00-00-00.000000"
        artifact_dir.mkdir()
        jtl_file = artifact_dir / "kpi.jtl"
        jtl_file.write_text(
            "timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success\n",
            encoding="utf-8",
        )
        result = find_latest_kpi("2026-*")
        assert result is not None
        assert result.name == "kpi.jtl"
        assert "2026-01-01" in str(result)

    def test_returns_latest_when_multiple_dirs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        for ts in ("2026-01-01_00-00-00.000000", "2026-02-01_00-00-00.000000"):
            d = tmp_path / ts
            d.mkdir()
            (d / "kpi.jtl").write_text(
                "timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success\n",
                encoding="utf-8",
            )
        result = find_latest_kpi("2026-*")
        # sorted reverse → "2026-02-…" comes first
        assert result is not None
        assert "2026-02" in str(result)
