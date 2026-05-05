from pathlib import Path
from analyze_results import (
    find_latest_kpi as find_latest_kpi_results,
    parse_args as parse_args_results,
)
import importlib.util
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

spec = importlib.util.spec_from_file_location(
    "analyze_kpi",
    str(Path(__file__).parent.parent / "analyze-kpi.py")
)
analyze_kpi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze_kpi)


def test_find_latest_kpi(tmp_path):
    # Tworzymy dwa katalogi z plikami kpi.jtl
    d1 = tmp_path / "2026-01-01_00-00-00.000000"
    d2 = tmp_path / "2026-01-02_00-00-00.000000"
    d1.mkdir()
    d2.mkdir()
    (d1 / "kpi.jtl").write_text("test1")
    (d2 / "kpi.jtl").write_text("test2")
    # Sprawdzamy, czy znajduje najnowszy
    find_latest_kpi = analyze_kpi.find_latest_kpi
    pattern = "2026-*"
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert find_latest_kpi(pattern).name == "kpi.jtl"
        assert find_latest_kpi_results(pattern).name == "kpi.jtl"
    finally:
        os.chdir(cwd)


def test_parse_args_defaults():
    parse_args = analyze_kpi.parse_args
    args = parse_args([])
    assert hasattr(args, "artifacts_pattern")
    args2 = parse_args_results([])
    assert hasattr(args2, "artifacts_pattern")
