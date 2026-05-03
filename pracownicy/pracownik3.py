"""
pracownik3.py — Autonomiczny agent pipeline z inteligentnym fallback.

Rozwiązuje problem niedostępnego klucza API OpenAI:
  - PRÓBUJE użyć AI (neochat) do generowania wpisu RUNBOOK
  - Jeśli AI NIEDOSTĘPNA (brak klucza, 401, timeout) → generuje wpis SAMODZIELNIE
    na podstawie danych z pliku JTL (bez AI)

Pipeline:
  1. Znajdź ostatni plik JTL (kpi.jtl / kfk.jtl)
  2. Parsuj metryki (samples, failures, czas)
  3. Wygeneruj wpis RUNBOOK (AI lub fallback)
  4. Zaktualizuj RUNBOOK-TAURUS.md
  5. Git commit + push
  6. Wyświetl URL do PR

Użycie:
  python pracownik3.py --pipeline
  python pracownik3.py --pipeline --branch main
  python pracownik3.py --diagnoza-ai
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
ROOT_DIR = Path(__file__).resolve().parent.parent

# ── Import AI (opcjonalny — nie blokujemy startu jeśli brak) ─────────────────
AI_DOSTEPNE = False
_load_config = None
_wyslij_do_ai = None

try:
    sys.path.insert(0, str(ROOT_DIR))
    sys.path.insert(0, str(Path.home() / "Desktop" / "moj-ai"))
    from neochat import load_config as _load_config, wyslij_do_ai as _wyslij_do_ai  # type: ignore
    AI_DOSTEPNE = True
except ImportError:
    pass  # AI niedostępna — użyjemy fallback


# ── Stałe ────────────────────────────────────────────────────────────────────
RUNBOOK_FILE = ROOT_DIR / "RUNBOOK-TAURUS.md"
PR_BASE_URL = "https://github.com/maxmae2211-cell/repo-gotowe/compare/main"

SYSTEM_PROMPT = (
    "Jesteś ekspertem od testowania wydajności. "
    "Specjalizujesz się w Taurus (bzt), JMeter i load testing. "
    "Odpowiadasz zwięźle, tylko dokładnie to co zostało poproszone."
)


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOZA AI
# ═══════════════════════════════════════════════════════════════════════════

def diagnozuj_ai() -> dict:
    """
    Sprawdza dostępność AI i zwraca słownik z wynikiem.
    Próbuje wysłać testowe zapytanie do modelu.
    """
    wynik = {
        "import_ok": AI_DOSTEPNE,
        "klucz_ok": False,
        "api_ok": False,
        "blad": None,
        "model": None,
    }

    if not AI_DOSTEPNE:
        wynik["blad"] = "Nie można zaimportować neochat.py"
        return wynik

    try:
        cfg = _load_config()
        klucz = cfg.get("api_key", "")
        wynik["model"] = cfg.get("model", "?")

        if not klucz or len(klucz) < 10:
            wynik["blad"] = "Klucz API pusty lub zbyt krótki"
            return wynik

        wynik["klucz_ok"] = True

        # Test API — krótkie zapytanie
        odpowiedz = _wyslij_do_ai(
            [{"role": "user", "content": "Odpowiedz jednym słowem: OK"}],
            cfg
        )
        if odpowiedz and "[BŁĄD]" not in odpowiedz:
            wynik["api_ok"] = True
        else:
            wynik["blad"] = odpowiedz

    except Exception as e:
        wynik["blad"] = str(e)

    return wynik


# ═══════════════════════════════════════════════════════════════════════════
# PARSOWANIE JTL
# ═══════════════════════════════════════════════════════════════════════════

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


def parsuj_jtl(plik: Path) -> dict:
    """Parsuje metryki z pliku JTL (CSV format Taurus/JMeter)."""
    if not plik.exists():
        return {}
    try:
        samples = []
        with open(plik, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(row)

        if not samples:
            return {}

        elapsed = [int(r.get("elapsed", 0)) for r in samples
                   if str(r.get("elapsed", "")).isdigit()]
        errors = sum(1 for r in samples
                     if str(r.get("success", "true")).lower() == "false")
        total = len(samples)

        metryki = {
            "total": total,
            "errors": errors,
            "error_rate_pct": round(errors / total * 100, 2) if total else 0,
            "avg_rt_ms": round(sum(elapsed) / len(elapsed), 1) if elapsed else 0,
        }

        # Czas trwania testu
        timestamps = [int(r.get("timeStamp", 0)) for r in samples
                      if str(r.get("timeStamp", "")).isdigit()]
        if timestamps:
            czas_ms = max(timestamps) - min(timestamps)
            czas_s = czas_ms // 1000
            metryki["duration_str"] = str(timedelta(seconds=czas_s))

        return metryki

    except Exception as e:
        return {"blad": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# GENEROWANIE WPISU RUNBOOK
# ═══════════════════════════════════════════════════════════════════════════

def generuj_wpis_fallback(plik_jtl: Path, metryki: dict) -> str:
    """
    Generuje wpis RUNBOOK BEZ AI — na podstawie danych z JTL.
    Format: - JMeter + Java8 run: PASS/FAIL (N samples, X% failures, duration T) -> Artifacts: `dir`
    """
    total = metryki.get("total", 0)
    error_rate = metryki.get("error_rate_pct", 0)
    duration = metryki.get("duration_str", "?")
    artifacts_dir = plik_jtl.parent.name

    status = "PASS" if error_rate <= 1.0 else "FAIL"

    return (
        f"- JMeter + Java8 run: {status} "
        f"({total} samples, {error_rate}% failures, duration {duration}) "
        f"-> Artifacts: `{artifacts_dir}`"
    )


def generuj_wpis_ai(plik_jtl: Path, metryki: dict) -> str | None:
    """
    Próbuje wygenerować wpis RUNBOOK używając AI.
    Zwraca wpis lub None jeśli AI niedostępna/błąd.
    """
    if not AI_DOSTEPNE:
        return None

    try:
        cfg = _load_config()
        if not cfg.get("api_key"):
            return None

        artifacts_dir = plik_jtl.parent.name
        kontekst = (
            f"Artefakty: {artifacts_dir}\n"
            f"Metryki: {json.dumps(metryki, ensure_ascii=False)}\n"
            f"Plik JTL: {plik_jtl.name}"
        )
        pytanie = (
            "Napisz JEDEN wpis do sekcji 'Latest verified pipeline results' w RUNBOOK-TAURUS.md. "
            "Format DOKŁADNIE: `- JMeter + Java8 run: PASS (<liczba> samples, <X>% failures, "
            "duration <czas>) -> Artifacts: \\`<dir>\\`` "
            "Podaj TYLKO tę jedną linię, nic więcej. "
            "Jeśli error_rate_pct > 1%, napisz FAIL zamiast PASS."
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Kontekst techniczny:\n{kontekst}"},
            {"role": "assistant", "content": "Rozumiem. Czekam na pytanie."},
            {"role": "user", "content": pytanie},
        ]

        odpowiedz = _wyslij_do_ai(messages, cfg)

        if odpowiedz and "[BŁĄD]" not in odpowiedz:
            # Wyodrębnij linię zaczynającą się od "- JMeter"
            for line in odpowiedz.splitlines():
                if line.strip().startswith("- JMeter"):
                    return line.strip()
            # Jeśli AI zwróciło coś w innym formacie — zwróć pierwszą linię
            return odpowiedz.strip().splitlines()[0]

    except Exception as e:
        print(f"       [AI] Błąd: {e}")

    return None


# ═══════════════════════════════════════════════════════════════════════════
# AKTUALIZACJA RUNBOOK
# ═══════════════════════════════════════════════════════════════════════════

def aktualizuj_runbook(nowy_wpis: str) -> bool:
    """Zastępuje linię JMeter+Java8 w RUNBOOK-TAURUS.md lub dopisuje nową."""
    if not RUNBOOK_FILE.exists():
        print(f"[BŁĄD] Nie znaleziono: {RUNBOOK_FILE}")
        return False

    tekst = RUNBOOK_FILE.read_text(encoding="utf-8")
    nowa_linia = nowy_wpis if nowy_wpis.startswith("- ") else f"- {nowy_wpis}"

    if re.search(r"^- JMeter \+ Java8 run:.*", tekst, re.MULTILINE):
        tekst = re.sub(
            r"^- JMeter \+ Java8 run:.*",
            nowa_linia,
            tekst,
            flags=re.MULTILINE
        )
    else:
        # Dopisz po nagłówku sekcji
        tekst = tekst.replace(
            "## Latest verified pipeline results\n",
            f"## Latest verified pipeline results\n{nowa_linia}\n"
        )

    RUNBOOK_FILE.write_text(tekst, encoding="utf-8")
    print(f"[OK]  RUNBOOK zaktualizowany")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# GIT
# ═══════════════════════════════════════════════════════════════════════════

def git_run(cmd: list) -> tuple[int, str, str]:
    """Uruchamia komendę git i zwraca (code, stdout, stderr)."""
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def git_commit_push(pliki: list, wiadomosc: str, branch: str = "qq") -> bool:
    """Wykonuje git add → commit → push."""
    # git add
    code, out, err = git_run(["git", "add"] + [str(p) for p in pliki])
    if code != 0:
        print(f"[BŁĄD] git add: {err}")
        return False

    # git commit
    code, out, err = git_run(["git", "commit", "-m", wiadomosc])
    if code != 0:
        if "nothing to commit" in (out + err):
            print("[INFO] Brak zmian do commitowania (nic się nie zmieniło).")
            return True
        print(f"[BŁĄD] git commit: {err}")
        return False
    print(f"[OK]  Commit: {out.splitlines()[0]}")

    # git push
    code, out, err = git_run(["git", "push", "origin", branch])
    if code != 0:
        print(f"[BŁĄD] git push: {err}")
        return False
    print(f"[OK]  Push → origin/{branch}")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# TRYBY
# ═══════════════════════════════════════════════════════════════════════════

def tryb_diagnoza_ai():
    """Wyświetla diagnozę dostępności AI."""
    print("\n[DIAGNOZA AI] Sprawdzam dostępność Neo AI...\n")
    d = diagnozuj_ai()

    print(f"  Import neochat.py : {'✓' if d['import_ok'] else '✗'}")
    print(f"  Klucz API         : {'✓ ustawiony' if d['klucz_ok'] else '✗ brak/pusty'}")
    print(f"  Model             : {d['model'] or 'nieznany'}")
    print(f"  Test API          : {'✓ DZIAŁA' if d['api_ok'] else '✗ BŁĄD'}")

    if d["blad"]:
        print(f"\n  Błąd: {d['blad']}")

    if not d["api_ok"]:
        print("\n  Rozwiązanie:")
        print("    cd C:\\Users\\maxma\\Desktop\\moj-ai")
        print("    python neochat.py --set-key sk-TWOJ_NOWY_KLUCZ")
        print("\n  Pipeline działa MIMO braku AI (tryb fallback).")
    else:
        print("\n  AI gotowa do pracy!")


def tryb_pipeline(branch: str = "qq") -> None:
    """
    Autonomiczny pipeline z inteligentnym fallback:
    1. Znajdź JTL
    2. Parsuj metryki
    3. Wygeneruj wpis RUNBOOK (AI jeśli dostępna, inaczej fallback)
    4. Zaktualizuj RUNBOOK-TAURUS.md
    5. Git commit + push (pliki: RUNBOOK + pracownik2.py + pracownik3.py + zadania.txt)
    6. Wyświetl URL PR
    """
    print("\n" + "═" * 60)
    print("  PRACOWNIK3 — Autonomiczny pipeline z fallback AI")
    print("═" * 60 + "\n")

    # Krok 1: Znajdź JTL
    plik_jtl = znajdz_ostatni_jtl()
    if plik_jtl is None:
        print("[BŁĄD] Brak pliku JTL. Uruchom najpierw testy: Taurus JMeter+Java8")
        return
    print(f"[1/5] JTL      : {plik_jtl.relative_to(BASE_DIR)}")

    # Krok 2: Parsuj metryki
    metryki = parsuj_jtl(plik_jtl)
    if not metryki or "blad" in metryki:
        print(f"[BŁĄD] Nie można sparsować JTL: {metryki.get('blad', 'pusty plik')}")
        return
    print(f"[2/5] Metryki  : {metryki['total']} samples, "
          f"{metryki['error_rate_pct']}% failures, "
          f"duration {metryki.get('duration_str', '?')}")

    # Krok 3: Generuj wpis RUNBOOK
    print("[3/5] Wpis RUNBOOK...")
    wpis = generuj_wpis_ai(plik_jtl, metryki)
    if wpis:
        print(f"       Źródło: AI ✓")
    else:
        wpis = generuj_wpis_fallback(plik_jtl, metryki)
        print(f"       Źródło: fallback (AI niedostępna)")
    print(f"       Wpis: {wpis}")

    # Krok 4: Zaktualizuj RUNBOOK
    print("[4/5] Aktualizuję RUNBOOK-TAURUS.md...")
    if not aktualizuj_runbook(wpis):
        return

    # Krok 5: Git commit + push
    print("[5/5] Commituje i pushuję...")
    dzisiaj = datetime.now().strftime("%Y-%m-%d")
    msg = f"pracownik3: RUNBOOK update JMeter+Java8 [{dzisiaj}]"

    # Pliki do commita: RUNBOOK + niezcommitowane workery/zadania
    pliki = ["RUNBOOK-TAURUS.md"]
    for p in ["pracownik2.py", "pracownik3.py", "zadania.txt"]:
        if (BASE_DIR / p).exists():
            pliki.append(p)

    ok = git_commit_push(pliki, msg, branch)

    if ok:
        pr_url = f"{PR_BASE_URL}...{branch}"
        print("\n" + "═" * 60)
        print("  PIPELINE UKOŃCZONY!")
        print(f"  PR URL: {pr_url}")
        print("═" * 60 + "\n")
    else:
        print("\n[BŁĄD] Pipeline przerwany na etapie git.")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Pracownik3 — Autonomiczny agent pipeline z fallback AI"
    )
    parser.add_argument(
        "--pipeline", action="store_true",
        help="Uruchom pełny pipeline: JTL → RUNBOOK → git commit+push → PR"
    )
    parser.add_argument(
        "--branch", default="qq",
        help="Branch git do pushowania (domyślnie: qq)"
    )
    parser.add_argument(
        "--diagnoza-ai", action="store_true",
        help="Sprawdź dostępność Neo AI i wyświetl diagnozę"
    )
    parser.add_argument(
        "--pokaz-metryki", action="store_true",
        help="Pokaż metryki ostatniego pliku JTL"
    )

    args = parser.parse_args()

    if args.diagnoza_ai:
        tryb_diagnoza_ai()
        return

    if args.pokaz_metryki:
        jtl = znajdz_ostatni_jtl()
        if jtl is None:
            print("[INFO] Brak pliku JTL.")
            return
        m = parsuj_jtl(jtl)
        print(f"Plik: {jtl}")
        print(json.dumps(m, indent=2, ensure_ascii=False))
        return

    if args.pipeline:
        tryb_pipeline(args.branch)
        return

    # Domyślnie: pokaż pomoc
    parser.print_help()
    print("\nWskazówka: uruchom z --pipeline aby wykonać pełny pipeline.")


if __name__ == "__main__":
    main()
