
# Zapewnia poprawny import main.py niezależnie od środowiska uruchomienia
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import hello


def test_hello():
    assert hello() == "Hello, world!"
