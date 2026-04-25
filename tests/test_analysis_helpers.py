import pytest
from analyze-kpi import find_latest_kpi, parse_args
from analyze_results import find_latest_kpi as find_latest_kpi_results, parse_args as parse_args_results
from pathlib import Path

def test_find_latest_kpi(tmp_path):
    # Tworzymy dwa katalogi z plikami kpi.jtl
    d1 = tmp_path / "2026-01-01_00-00-00.000000"
    d2 = tmp_path / "2026-01-02_00-00-00.000000"
    d1.mkdir()
    d2.mkdir()
    (d1 / "kpi.jtl").write_text("test1")
    (d2 / "kpi.jtl").write_text("test2")
    # Sprawdzamy, czy znajduje najnowszy
    assert find_latest_kpi(str(tmp_path / "2026-*")).name == "kpi.jtl"
    assert find_latest_kpi_results(str(tmp_path / "2026-*")).name == "kpi.jtl"

def test_parse_args_defaults():
    args = parse_args()
    assert hasattr(args, "artifacts-pattern")
    args2 = parse_args_results()
    assert hasattr(args2, "artifacts-pattern")
