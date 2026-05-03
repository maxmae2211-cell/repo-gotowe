"""
pracownik5.py — Specjalista ds. Aktualizacji i Rozbudowy Projektu

Rola: Autonomiczny agent odpowiedzialny za:
  - analizę i aktualizację bibliotek (requirements.txt)
  - planowanie sprintów i nowych funkcji
  - audyt kodu i rekomendacje ulepszeń
  - migracje, refaktoryzację i modernizację projektu
  - raportowanie statusu aktualizacji

Użycie:
  python pracownik5.py                          # zadania z pliku zadania-aktualizacja.txt
  python pracownik5.py "Sprawdź requirements"   # jedno zadanie z CLI
  python pracownik5.py --zadania moj_plik.txt   # własny plik zadań
  python pracownik5.py --raport wyniki.txt      # własny plik raportu
  python pracownik5.py --pokaz-raport           # wyświetl ostatni raport
  python pracownik5.py --szkolenie              # uruchom pełny tryb szkoleniowy
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from neochat import load_config
except ImportError:
    print("[BŁĄD] Brak pliku neochat.py — pracownik5.py wymaga neochat.py w tym samym folderze.")
    sys.exit(1)

try:
    from ai_backend import wyslij_do_ai_multi
except ImportError:
    wyslij_do_ai_multi = None

try:
    from moderacja import sprawdz_wejscie, sprawdz_wyjscie
except ImportError:
    def sprawdz_wejscie(tekst): return None
    def sprawdz_wyjscie(tekst): return tekst


# ── Ścieżki ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ZADANIA_FILE = BASE_DIR / "zadania-aktualizacja.txt"
RAPORT_FILE = BASE_DIR / "raport-aktualizacja.txt"

# ── Tożsamość pracownika ──────────────────────────────────────────────────────
IMIE = "Pracownik5 (Specjalista Aktualizacji)"

SYSTEM_PROMPT = (
    "Jesteś Pracownikiem5 — specjalistą ds. aktualizacji, rozbudowy i ulepszania projektów programistycznych. "
    "Twoje kompetencje to: "
    "1) Analiza bibliotek Python i rekomendacje aktualizacji w requirements.txt, "
    "2) Audyt kodu — wykrywanie przestarzałych wzorców, potencjalnych bugów i miejsc do refaktoryzacji, "
    "3) Planowanie sprintów — rozbijanie dużych celów na konkretne, małe zadania gotowe do implementacji, "
    "4) Modernizacja architektury — migracje do nowych wersji API, nowych bibliotek, nowych wzorców, "
    "5) Raportowanie statusu — tworzenie zwięzłych raportów postępu i rekomendacji. "
    "Pracujesz autonomicznie. Odpowiadasz konkretnie, technicznie i zwięźle. "
    "Zawsze kończysz zadanie w jednej odpowiedzi. Jeśli zadanie wymaga kodu — piszesz gotowy kod. "
    "Jeśli wymaga listy — dajesz gotową listę z priorytetami. Nie pytasz — działasz."
)

PROGRAM_SZKOLENIOWY = [
    "Przeanalizuj plik requirements.txt w tym projekcie i podaj, które biblioteki mają nowsze wersje oraz czy są bezpieczne do aktualizacji. Podaj konkretne komendy pip do aktualizacji.",
    "Zaproponuj plan Sprint 1 dla projektu AI chatbot (moj-ai) z 5 konkretnymi zadaniami techniczymi, z opisem, priorytetem (H/M/L) i szacunkiem w godzinach.",
    "Przygotuj plan modernizacji ai_backend.py: co warto dodać, co uprościć, jakie nowe funkcje by zwiększyły niezawodność. Podaj 5 konkretnych propozycji z uzasadnieniem.",
    "Napisz skrypt Python check_updates.py który sprawdza dostępne aktualizacje bibliotek z requirements.txt i wyświetla raport: aktualna wersja vs. najnowsza dostępna.",
    "Zaproponuj strukturę pliku CHANGELOG.md dla tego projektu i wypełnij go wpisami za ostatnie 3 miesiące (fikcyjne ale realistyczne).",
]


# ── Wykonanie pojedynczego zadania ─────────────────────────────────────────────
def wykonaj_zadanie(zadanie: str, cfg: dict) -> str:
    blokada = sprawdz_wejscie(zadanie)
    if blokada:
        return f"[MODERACJA — ZABLOKOWANO] {blokada}"

    cfg_pracownik = {**cfg, "system_prompt": SYSTEM_PROMPT}
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": zadanie},
    ]

    if wyslij_do_ai_multi:
        wynik = wyslij_do_ai_multi(messages, cfg_pracownik)
    else:
        from neochat import wyslij_do_ai
        wynik = wyslij_do_ai(messages, cfg_pracownik)

    if wynik is None:
        return "[BŁĄD] Brak odpowiedzi od AI."

    return sprawdz_wyjscie(wynik)


# ── Wczytaj zadania z pliku ────────────────────────────────────────────────────
def wczytaj_zadania(sciezka: Path) -> list[str]:
    if not sciezka.exists():
        print(f"[INFO] Brak pliku zadań: {sciezka}")
        return []
    linie = sciezka.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in linie if l.strip() and not l.startswith("#")]


# ── Zapisz raport ──────────────────────────────────────────────────────────────
def zapisz_raport(wyniki: list[dict], sciezka: Path) -> None:
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linie = [f"RAPORT — {IMIE} — {teraz}", "=" * 60, ""]
    for i, w in enumerate(wyniki, 1):
        linie.append(f"ZADANIE {i}: {w['zadanie']}")
        linie.append("-" * 40)
        linie.append(w["wynik"])
        linie.append("")
    sciezka.write_text("\n".join(linie), encoding="utf-8")
    print(f"\n[✓] Raport zapisany: {sciezka}")


# ── Główna pętla zadań ─────────────────────────────────────────────────────────
def uruchom(zadania: list[str], cfg: dict, sciezka_raportu: Path) -> None:
    if not zadania:
        print("[INFO] Brak zadań do wykonania.")
        return

    wyniki = []
    print(f"\n{IMIE}\n{'=' * 60}")
    print(f"Zadań do wykonania: {len(zadania)}\n")

    for i, zadanie in enumerate(zadania, 1):
        print(f"[{i}/{len(zadania)}] {zadanie[:80]}{'...' if len(zadanie) > 80 else ''}")
        print("Analizuję...", end="", flush=True)
        try:
            wynik = wykonaj_zadanie(zadanie, cfg)
        except Exception as e:
            wynik = f"[BŁĄD] {e}"
        print(f"\r[✓] Gotowe!   ")
        print(f"{wynik}\n{'-' * 40}")
        wyniki.append({"zadanie": zadanie, "wynik": wynik})

    zapisz_raport(wyniki, sciezka_raportu)


# ── CLI ────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{IMIE} — specjalista ds. aktualizacji i rozbudowy"
    )
    parser.add_argument("zadanie", nargs="?", default=None, help="Jedno zadanie z CLI")
    parser.add_argument("--zadania", metavar="PLIK", default=str(ZADANIA_FILE),
                        help=f"Plik z zadaniami (domyślnie: {ZADANIA_FILE.name})")
    parser.add_argument("--raport", metavar="PLIK", default=str(RAPORT_FILE),
                        help=f"Plik raportu (domyślnie: {RAPORT_FILE.name})")
    parser.add_argument("--pokaz-raport", action="store_true", help="Wyświetl ostatni raport")
    parser.add_argument("--szkolenie", action="store_true",
                        help="Uruchom program szkoleniowy (5 zadań specjalistycznych)")

    args = parser.parse_args()
    raport_sciezka = Path(args.raport)

    if args.pokaz_raport:
        if raport_sciezka.exists():
            print(raport_sciezka.read_text(encoding="utf-8"))
        else:
            print(f"[INFO] Brak raportu: {raport_sciezka}")
        return

    cfg = load_config()

    if args.szkolenie:
        print(f"\n[SZKOLENIE] Uruchamiam program szkoleniowy dla {IMIE}")
        raport_sciezka = BASE_DIR / "raport-szkolenie-aktualizacja.txt"
        uruchom(PROGRAM_SZKOLENIOWY, cfg, raport_sciezka)
    elif args.zadanie:
        uruchom([args.zadanie], cfg, raport_sciezka)
    else:
        zadania = wczytaj_zadania(Path(args.zadania))
        uruchom(zadania, cfg, raport_sciezka)


if __name__ == "__main__":
    main()
