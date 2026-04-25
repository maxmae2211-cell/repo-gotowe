
import sys
import os
import pytest
from pathlib import Path

# Dodaj katalog główny repo do sys.path, by import działał lokalnie i w CI
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from analyze_results import find_latest_kpi


def test_find_latest_kpi(tmp_path):
    # Przygotuj strukturę katalogów i plików
    d1 = tmp_path / "2026-01-01_00-00-00.000000"
    d1.mkdir()
    (d1 / "kpi.jtl").write_text("test")
    d2 = tmp_path / "2026-01-02_00-00-00.000000"
    d2.mkdir()
    (d2 / "kpi.jtl").write_text("test2")
    # Najnowszy katalog powinien być wybrany
    result = find_latest_kpi(str(tmp_path / "2026-*"))
    assert result is not None
    assert result.parent.name == "2026-01-02_00-00-00.000000"
    assert result.name == "kpi.jtl"
