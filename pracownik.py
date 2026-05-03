"""
pracownik.py — Autonomiczny agent AI (Pracownik) oparty na NeoChat/OpenAI.

Pracownik przyjmuje listę zadań i wykonuje je automatycznie, jedno po drugim,
korzystając z OpenAI API. Wyniki zapisuje do pliku raportu.

Użycie:
  python pracownik.py                          # zadania z pliku zadania.txt
  python pracownik.py "Napisz email do szefa"  # jedno zadanie z CLI
  python pracownik.py --zadania zadania.txt     # własny plik zadań
  python pracownik.py --raport wyniki.txt       # własny plik raportu
  python pracownik.py --pokaz-raport            # wyświetl ostatni raport
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    from neochat import load_config
except ImportError:
    print(
        "[BŁĄD] Brak pliku neochat.py — pracownik.py wymaga neochat.py w tym samym folderze."
    )
    sys.exit(1)

try:
    from ai_backend import wyslij_do_ai_multi
except ImportError:
    wyslij_do_ai_multi = None

try:
    from moderacja import sprawdz_wejscie, sprawdz_wyjscie
except ImportError:

    def sprawdz_wejscie(tekst):
        return None

    def sprawdz_wyjscie(tekst):
        return tekst


# ── Ścieżki ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ZADANIA_FILE = BASE_DIR / "zadania.txt"
RAPORT_FILE = BASE_DIR / "raport-pracownik.txt"

# ── System prompt pracownika ─────────────────────────────────────────────────
SYSTEM_PROMPT_PRACOWNIK = (
    "Jesteś autonomicznym pracownikiem AI. Dostajesz konkretne zadanie i wykonujesz je "
    "bez dodatkowych pytań. Odpowiadasz konkretnie, zwięźle i merytorycznie. "
    "Jeśli zadanie wymaga kodu — piszesz kod. Jeśli wymaga tekstu — piszesz tekst. "
    "Zawsze kończysz zadanie w jednej odpowiedzi."
)


# ── Wykonanie pojedynczego zadania ────────────────────────────────────────────
def wykonaj_zadanie(zadanie: str, cfg: dict) -> str:
    """Wysyła jedno zadanie do AI i zwraca wynik."""
    blokada = sprawdz_wejscie(zadanie)
    if blokada:
        return f"[MODERACJA — ZABLOKOWANO] {blokada}"

    # Nadpisujemy system prompt na wersję pracownika
    cfg_pracownik = {**cfg, "system_prompt": SYSTEM_PROMPT_PRACOWNIK}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PRACOWNIK},
        {"role": "user", "content": zadanie},
    ]
    if wyslij_do_ai_multi:
        wynik = wyslij_do_ai_multi(messages, cfg_pracownik)
    else:
        from neochat import wyslij_do_ai

        wynik = wyslij_do_ai(messages, cfg_pracownik)

    if wynik is None:
        return "[BŁĄD] Brak odpowiedzi od AI."

    wynik = sprawdz_wyjscie(wynik)
    return wynik


# ── Wczytaj zadania z pliku ───────────────────────────────────────────────────
def wczytaj_zadania(sciezka: Path) -> list[str]:
    """Wczytuje zadania z pliku — każda linia to jedno zadanie (puste pomijane)."""
    if not sciezka.exists():
        print(f"[INFO] Brak pliku zadań: {sciezka}")
        print("[INFO] Utwórz plik zadania.txt — każda linia to jedno zadanie.")
        return []
    linie = sciezka.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in linie if l.strip() and not l.startswith("#")]


# ── Zapisz raport ─────────────────────────────────────────────────────────────
def zapisz_raport(wyniki: list[dict], sciezka: Path) -> None:
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linie = [f"RAPORT PRACOWNIKA — {teraz}", "=" * 60, ""]
    for i, w in enumerate(wyniki, 1):
        linie.append(f"ZADANIE {i}: {w['zadanie']}")
        linie.append("-" * 40)
        linie.append(w["wynik"])
        linie.append("")
    sciezka.write_text("\n".join(linie), encoding="utf-8")
    print(f"\n[✓] Raport zapisany: {sciezka}")


# ── Główna pętla zadań ────────────────────────────────────────────────────────
def uruchom(zadania: list[str], cfg: dict, sciezka_raportu: Path) -> None:
    if not zadania:
        print("[INFO] Brak zadań do wykonania.")
        return

    wyniki = []
    print(f"\nPRACOWNIK AI — {len(zadania)} zadanie(a) do wykonania\n{'=' * 50}")

    for i, zadanie in enumerate(zadania, 1):
        print(
            f"\n[{i}/{len(zadania)}] ZADANIE: {zadanie[:80]}{'...' if len(zadanie) > 80 else ''}"
        )
        print("Pracuję...", end="", flush=True)
        wynik = wykonaj_zadanie(zadanie, cfg)
        print(f"\r[✓] Gotowe!   ")
        print(f"WYNIK:\n{wynik}\n{'-' * 40}")
        wyniki.append({"zadanie": zadanie, "wynik": wynik})

    zapisz_raport(wyniki, sciezka_raportu)


# ── Wyświetl raport ───────────────────────────────────────────────────────────
def pokaz_raport(sciezka: Path) -> None:
    if not sciezka.exists():
        print(f"[INFO] Brak raportu: {sciezka}")
        return
    print(sciezka.read_text(encoding="utf-8"))


# ── CLI ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pracownik AI — autonomiczny agent wykonujący zadania"
    )
    parser.add_argument(
        "zadanie",
        nargs="?",
        default=None,
        help="Jedno zadanie z linii poleceń (opcjonalne)",
    )
    parser.add_argument(
        "--zadania",
        metavar="PLIK",
        default=str(ZADANIA_FILE),
        help=f"Plik z zadaniami (domyślnie: {ZADANIA_FILE.name})",
    )
    parser.add_argument(
        "--raport",
        metavar="PLIK",
        default=str(RAPORT_FILE),
        help=f"Plik raportu (domyślnie: {RAPORT_FILE.name})",
    )
    parser.add_argument(
        "--pokaz-raport", action="store_true", help="Wyświetl ostatni raport"
    )

    args = parser.parse_args()

    raport_sciezka = Path(args.raport)

    if args.pokaz_raport:
        pokaz_raport(raport_sciezka)
        return

    cfg = load_config()
    if args.zadanie:
        # Jedno zadanie z CLI
        zadania = [args.zadanie]
    else:
        # Zadania z pliku
        zadania = wczytaj_zadania(Path(args.zadania))

    uruchom(zadania, cfg, raport_sciezka)


if __name__ == "__main__":
    main()
