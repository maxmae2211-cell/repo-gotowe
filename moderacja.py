"""
moderacja.py — TWOJE własne reguły moderacji dla NeoChat.

Dwie funkcje do edycji:
  sprawdz_wejscie(tekst)  → sprawdza wiadomość użytkownika PRZED wysłaniem do AI
  sprawdz_wyjscie(tekst)  → sprawdza/modyfikuje odpowiedź AI PRZED wyświetleniem

Jeśli chcesz ZABLOKOWAĆ wiadomość — zwróć string z powodem.
Jeśli chcesz PRZEPUŚCIĆ wiadomość — zwróć None (wejście) lub tekst bez zmian (wyjście).

Możesz tu dodać:
  - listę zabronionych słów/fraz
  - własne reguły regex
  - wywołanie własnego API moderacji
  - logowanie zapytań do pliku
  - własne limity długości
  - cokolwiek chcesz!
"""

import logging
from pathlib import Path

# ── Opcjonalne logowanie zapytań ──────────────────────────────────────────────
LOG_FILE = Path(__file__).parent / "historia.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    encoding="utf-8"
)


# ─────────────────────────────────────────────────────────────────────────────
# SEKCJA 1: TWOJE ZABRONIONE FRAZY / SŁOWA
# Dodaj własne słowa lub frazy — wiadomość zostanie zablokowana.
# ─────────────────────────────────────────────────────────────────────────────

# Brak zabronionych słów — moderacja wyłączona
ZABRONIONE_WEJSCIE: list[str] = []

ZABRONIONE_WYJSCIE: list[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# SEKCJA 2: WŁASNE REGUŁY REGEX
# Pattern → komunikat blokady (wejście) lub zamiana (wyjście)
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# GŁÓWNE FUNKCJE — możesz je modyfikować dowolnie
# ─────────────────────────────────────────────────────────────────────────────

def sprawdz_wejscie(tekst: str) -> str | None:
    """
    Sprawdza wiadomość użytkownika PRZED wysłaniem do AI.
    Zwraca:
      None   — wiadomość OK, przepuść
      str    — powód blokady (wiadomość NIE zostanie wysłana do AI)
    """
    logging.info(f"WEJŚCIE: {tekst[:200]}")
    return None  # brak blokad


def sprawdz_wyjscie(tekst: str) -> str:
    """
    Sprawdza/modyfikuje odpowiedź AI PRZED wyświetleniem użytkownikowi.
    Zwraca zawsze str — możesz zwrócić oryginalny tekst lub zmodyfikowany.
    """
    logging.info(f"WYJŚCIE: {tekst[:200]}")
    return tekst  # brak cenzury — odpowiedź bez zmian
