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
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

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
    """Szuka najnowszego pliku kpi.jtl lub kfk.jtl w katalogach z timestampami."""
    pattern = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"
    dirs = sorted(
        [d for d in ROOT_DIR.iterdir() if d.is_dir() and re.match(pattern, d.name)],
        reverse=True
    )
    for d in dirs:
        for nazwa in ("kpi.jtl", "kfk.jtl"):
            jtl = d / nazwa
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


def generuj_wpis_runbook(cfg: dict, plik_jtl: Path | None = None) -> str:
    """Prosi AI o nowy wpis do RUNBOOK na podstawie wyników JTL."""
    if plik_jtl is None:
        plik_jtl = znajdz_ostatni_jtl()

    if plik_jtl is None:
        return ""

    metryki = wczytaj_wyniki_jtl(plik_jtl)
    if not metryki:
        return ""

    # Wykryj typ runu z nazwy katalogu artefaktów
    artifacts_dir = plik_jtl.parent.name
    kontekst = (
        f"Artefakty: {artifacts_dir}\n"
        f"Metryki: {json.dumps(metryki, ensure_ascii=False)}\n"
        f"Plik JTL: {plik_jtl.name}"
    )
    pytanie = (
        "Napisz JEDEN wpis do sekcji 'Latest verified pipeline results' w RUNBOOK-TAURUS.md. "
        "Format: `- JMeter + Java8 run: PASS (<liczba> samples, <X>% failures, duration <czas>) -> Artifacts: \\`<dir>\\`` "
        "Podaj TYLKO tę linię, nic więcej. Jeśli error_rate_pct > 1%, napisz FAIL zamiast PASS."
    )
    return zapytaj_ai(pytanie, cfg, kontekst).strip()


def aktualizuj_runbook(nowy_wpis: str) -> bool:
    """Zastępuje linię JMeter+Java8 w RUNBOOK-TAURUS.md nowym wpisem (generowanym przez AI)."""
    runbook = ROOT_DIR / "RUNBOOK-TAURUS.md"
    if not runbook.exists():
        print(f"[BŁĄD] Nie znaleziono: {runbook}")
        return False

    tekst = runbook.read_text(encoding="utf-8")

    # Zastąp istniejącą linię JMeter+Java8 lub dopisz po linii Standard
    import re as _re
    nowa_linia = nowy_wpis if nowy_wpis.startswith("- ") else f"- {nowy_wpis}"

    if _re.search(r"^- JMeter \+ Java8 run:.*", tekst, _re.MULTILINE):
        tekst = _re.sub(
            r"^- JMeter \+ Java8 run:.*",
            nowa_linia,
            tekst,
            flags=_re.MULTILINE
        )
    else:
        # Dopisz po sekcji Latest verified
        tekst = tekst.replace(
            "## Latest verified pipeline results\n",
            f"## Latest verified pipeline results\n{nowa_linia}\n"
        )

    runbook.write_text(tekst, encoding="utf-8")
    print(f"[OK] RUNBOOK zaktualizowany: {nowa_linia}")
    return True


def git_commit_push(
    pliki: list,
    wiadomosc: str,
    branch: str = "qq"
) -> bool:
    """Wykonuje git add, commit i push dla podanych plików."""
    import subprocess

    def run(cmd):
        r = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(ROOT_DIR)
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()

    # git add
    code, out, err = run(["git", "add"] + [str(p) for p in pliki])
    if code != 0:
        print(f"[BŁĄD] git add: {err}")
        return False

    # git commit
    code, out, err = run(["git", "commit", "-m", wiadomosc])
    if code != 0:
        if "nothing to commit" in out + err:
            print("[INFO] Brak zmian do commitowania.")
            return True
        print(f"[BŁĄD] git commit: {err}")
        return False
    print(f"[OK] Commit: {out.splitlines()[0] if out else wiadomosc}")

    # git push
    code, out, err = run(["git", "push", "origin", branch])
    if code != 0:
        print(f"[BŁĄD] git push: {err}")
        return False
    print(f"[OK] Push → origin/{branch}")
    return True


def tryb_pipeline(cfg: dict, branch: str = "qq") -> None:
    """Autonomiczny tryb pipeline:
    1. Znajdź ostatni JTL
    2. Wygeneruj wpis do RUNBOOK (AI)
    3. Zaktualizuj RUNBOOK-TAURUS.md
    4. git commit + push
    5. Wyświetl URL do PR
    """
    from datetime import datetime as _dt
    print("\n[PIPELINE] Autonomiczny agent Taurus startuje...\n")

    # Krok 1: JTL
    plik_jtl = znajdz_ostatni_jtl()
    if plik_jtl is None:
        print("[BŁĄD] Brak pliku JTL. Uruchom najpierw testy Taurus.")
        return
    print(f"[1/4] Znaleziono wyniki: {plik_jtl}")

    # Krok 2: AI generuje wpis RUNBOOK
    print("[2/4] Generuję wpis RUNBOOK (AI)...")
    wpis = generuj_wpis_runbook(cfg, plik_jtl)
    if not wpis:
        print("[BŁĄD] AI nie wygenerowało wpisu. Sprawdź klucz API.")
        return
    print(f"       Wpis: {wpis}")

    # Krok 3: Aktualizacja RUNBOOK
    print("[3/4] Aktualizuję RUNBOOK-TAURUS.md...")
    if not aktualizuj_runbook(wpis):
        return

    # Krok 4: git commit + push
    print("[4/4] Commituje i pushuje zmiany...")
    teraz = _dt.now().strftime("%Y-%m-%d")
    msg = f"pracownik2: aktualizacja RUNBOOK JMeter+Java8 [{teraz}]"
    ok = git_commit_push(["RUNBOOK-TAURUS.md"], msg, branch)

    if ok:
        pr_url = f"https://github.com/maxmae2211-cell/repo-gotowe/compare/main...{branch}"
        print(f"\n[DONE] Pipeline ukończony!")
        print(f"       PR URL: {pr_url}")



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
    parser.add_argument("--pipeline", action="store_true",
                        help="Autonomiczny pipeline: JTL → AI → RUNBOOK → git commit+push → PR URL")
    parser.add_argument("--branch", default="qq",
                        help="Branch git do pushowania (domyślnie: qq)")

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

    if args.pipeline:
        tryb_pipeline(cfg, branch=args.branch)
        return

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
