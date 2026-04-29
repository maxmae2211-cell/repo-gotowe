
# Zapewnia poprawny import main.py niezależnie od środowiska uruchomienia
from main import hello
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


def test_hello():
    assert hello() == "Hello, world!"
