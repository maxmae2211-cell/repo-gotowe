"""
Pytest fixtures dla testów projektu repo-gotowe.
"""
import sys
from pathlib import Path

# Dodaj root projektu do sys.path żeby importy działały
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
