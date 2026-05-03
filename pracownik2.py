"""
pracownik2.py — Autonomiczny agent AI do zadań Taurus pipeline.

Obsługuje:
- Analizę wyników testów Taurus (JTL/JSON)
- Generowanie komentarzy do RUNBOOK-TAURUS.md
- Sugestie dla PR (qq → main)
- Ogólne pytania o wydajność i load testing

Używa neochat.py jako warstwy AI (load_config + wyslij_do_ai).
Klucz API: Desktop/moj-ai/config.json lub lokalny config.json lub env OPENAI_API_KEY
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Import z neochat (w tym samym repo)
try:
    from neochat import load_config, wyslij_do_ai
except ImportError:
    print("[BŁĄD] Nie znaleziono neochat.py. Upewnij się że jesteś w katalogu repo-gotowe.")
    sys.exit(1)

# Import moderacji (opcjonalny)
try:
    from moderacja import sprawdz_wejscie, sprawdz_wyjscie
except ImportError:
    def sprawdz_wejscie(t): return None
    def sprawdz_wyjscie(t): return t

RAPORT_FILE = BASE_DIR / "raport-pracownik2.txt"

SYSTEM_PROMPT = (
    "Jesteś ekspertem od testowania wydajności i automatyzacji CI/CD. "
    "Specjalizujesz się w Taurus (bzt), JMeter, load testing, i analizie wyników testów. "
    "Odpowiadasz po polsku, zwięźle i merytorycznie. "
    "Pomagasz analizować wyniki testów, pisać opisy do RUNBOOK, komentarze do PR, "
    "i sugerować optymalizacje na podstawie danych o wydajności."
)


def zapytaj_ai(pytanie: str, cfg: dict, kontekst: str = "") -> str:
    """Wysyła pytanie do AI z opcjonalnym kontekstem technicznym."""
    blokada = sprawdz_wejscie(pytanie)
    if blokada:
        return f"[MODERACJA] {blokada}"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if kontekst:
        messages.append({
            "role": "user",
            "content": f"Kontekst techniczny:\n{kontekst}"
        })
        messages.append({
            "role": "assistant",
            "content": "Rozumiem kontekst. Czekam na Twoje pytanie."
        })

    messages.append({"role": "user", "content": pytanie})

    odpowiedz = wyslij_do_ai(messages, cfg)
    return sprawdz_wyjscie(odpowiedz)


def wczytaj_wyniki_jtl(plik: Path) -> dict:
    """Parsuje podstawowe metryki z pliku JTL (CSV format Taurus)."""
    if not plik.exists():
        return {}
    try:
        import csv
        samples = []
        with open(plik, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(row)
        if not samples:
            return {}

        # Zbierz metryki
        elapsed = [int(r.get("elapsed", 0)) for r in samples if r.get("elapsed", "").isdigit()]
        errors = sum(1 for r in samples if r.get("success", "true").lower() == "false")
        total = len(samples)

        metryki = {
            "total": total,
            "errors": errors,
            "error_rate_pct": round(errors / total * 100, 2) if total else 0,
            "avg_rt_ms": round(sum(elapsed) / len(elapsed), 1) if elapsed else 0,
            "min_rt_ms": min(elapsed) if elapsed else 0,
            "max_rt_ms": max(elapsed) if elapsed else 0,
        }
        # Percentyle
        if elapsed:
            s = sorted(elapsed)
            metryki["p90_ms"] = s[int(len(s) * 0.9)]
            metryki["p95_ms"] = s[int(len(s) * 0.95)]
        return metryki
    except Exception as e:
        return {"blad_parsowania": str(e)}


def znajdz_ostatni_jtl() -> Path | None:
    """Szuka najnowszego pliku kfk.jtl w katalogach z timestampami."""
    pattern = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"
    dirs = sorted(
        [d for d in BASE_DIR.iterdir() if d.is_dir() and re.match(pattern, d.name)],
        reverse=True
    )
    for d in dirs:
        jtl = d / "kfk.jtl"
        if jtl.exists():
            return jtl
    return None


def analizuj_wyniki(cfg: dict, plik_jtl: Path | None = None) -> str:
    """Analizuje wyniki testów i zwraca komentarz AI."""
    if plik_jtl is None:
        plik_jtl = znajdz_ostatni_jtl()

    if plik_jtl is None:
        return "[INFO] Nie znaleziono pliku JTL z wynikami testów."

    metryki = wczytaj_wyniki_jtl(plik_jtl)
    if not metryki:
        return f"[INFO] Plik {plik_jtl} jest pusty lub nieparsywalny."

    kontekst = f"Wyniki testu Taurus z pliku: {plik_jtl.name}\nMetryki: {json.dumps(metryki, ensure_ascii=False)}"
    pytanie = (
        "Na podstawie powyższych metryk: "
        "1) Oceń ogólną jakość testu (dobry/średni/zły). "
        "2) Wskaż co warto poprawić. "
        "3) Napisz krótki (3-4 zdania) wpis do RUNBOOK opisujący ten run. "
        "Formatuj jako: OCENA: ...\nWNIOSKI: ...\nRUNBOOK WPIS: ..."
    )
    return zapytaj_ai(pytanie, cfg, kontekst)


def generuj_opis_pr(cfg: dict, branch: str = "qq", target: str = "main") -> str:
    """Generuje opis PR dla zmian Taurus pipeline."""
    # Zbierz info o ostatnim przebiegu
    metryki_str = ""
    plik_jtl = znajdz_ostatni_jtl()
    if plik_jtl:
        m = wczytaj_wyniki_jtl(plik_jtl)
        if m:
            metryki_str = f"\nOstatni run: {m.get('total',0)} próbek, błędy {m.get('error_rate_pct',0)}%, avg RT {m.get('avg_rt_ms',0)}ms"

    pytanie = (
        f"Napisz zwięzły opis Pull Request dla brancha `{branch}` → `{target}` "
        f"w projekcie load testing (Taurus/bzt).{metryki_str}\n"
        "PR zawiera: konfiguracje testów Taurus, skrypty PowerShell do uruchamiania, "
        "aktualizacje RUNBOOK-TAURUS.md, i pliki AI asystenta (neochat, pracownik).\n"
        "Format: 3-4 zdania po polsku, opisz co zostało zrobione i dlaczego."
    )
    return zapytaj_ai(pytanie, cfg)


def tryb_interaktywny(cfg: dict):
    """Interaktywna sesja z agentem Taurus."""
    print("=" * 55)
    print("  Pracownik2 — Agent Taurus Pipeline")
    print("  Wpisz 'exit', 'analiza' lub 'pr' dla skrótów")
    print("=" * 55)

    while True:
        try:
            tekst = input("\nTy: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nDo widzenia!")
            break

        if not tekst:
            continue
        if tekst.lower() in ("exit", "quit", "koniec"):
            print("Do widzenia!")
            break
        if tekst.lower() == "analiza":
            wynik = analizuj_wyniki(cfg)
        elif tekst.lower() == "pr":
            wynik = generuj_opis_pr(cfg)
        else:
            wynik = zapytaj_ai(tekst, cfg)

        print(f"\nPracownik2: {wynik}")


def zapisz_do_raportu(tresc: str):
    """Dopisuje wynik do raport-pracownik2.txt."""
    with open(RAPORT_FILE, "a", encoding="utf-8") as f:
        f.write(tresc + "\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Pracownik2 — Agent AI do zadań Taurus pipeline"
    )
    parser.add_argument("pytanie", nargs="?", help="Jednorazowe pytanie do agenta")
    parser.add_argument("--analiza", action="store_true",
                        help="Analizuj wyniki ostatniego testu JTL")
    parser.add_argument("--jtl", metavar="PLIK", help="Ścieżka do pliku .jtl do analizy")
    parser.add_argument("--pr", action="store_true",
                        help="Generuj opis PR (qq → main)")
    parser.add_argument("--raport", action="store_true",
                        help="Zapisz wynik do raport-pracownik2.txt")
    parser.add_argument("--pokaz-raport", action="store_true",
                        help="Pokaż zawartość raport-pracownik2.txt")

    args = parser.parse_args()

    if args.pokaz_raport:
        if RAPORT_FILE.exists():
            print(RAPORT_FILE.read_text(encoding="utf-8"))
        else:
            print("[INFO] Raport jest pusty.")
        return

    cfg = load_config()

    if not cfg.get("api_key"):
        print("[BŁĄD] Brak klucza API OpenAI!")
        print("Ustaw go w jednym z miejsc:")
        print(f"  1. python neochat.py --set-key sk-TWOJ_KLUCZ")
        print(f"  2. Edytuj: C:\\Users\\{os.getenv('USERNAME')}\\Desktop\\moj-ai\\config.json")
        print(f"  3. Ustaw zmienną: $env:OPENAI_API_KEY = 'sk-KLUCZ'")
        sys.exit(1)

    wynik = None

    if args.analiza or args.jtl:
        plik = Path(args.jtl) if args.jtl else None
        wynik = analizuj_wyniki(cfg, plik)
        print(wynik)

    elif args.pr:
        wynik = generuj_opis_pr(cfg)
        print(wynik)

    elif args.pytanie:
        wynik = zapytaj_ai(args.pytanie, cfg)
        print(wynik)

    else:
        tryb_interaktywny(cfg)
        return

    if args.raport and wynik:
        zapisz_do_raportu(wynik)
        print(f"\n[OK] Zapisano do: {RAPORT_FILE}")


if __name__ == "__main__":
    main()
