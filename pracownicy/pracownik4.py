"""
pracownik4.py — Finder AI: szuka działającego backendu AI
==========================================================
Diagnozuje dostępne providery AI i zwraca pierwszy działający.
Wielokrotnego użytku — NIE modyfikuje żadnych plików.

Strategie (kolejność prób):
  1. Zmienna środowiskowa OPENAI_API_KEY
  2. Zmienna środowiskowa GROQ_API_KEY (darmowy)
  3. Ollama lokalnie (http://localhost:11434)
  4. LM Studio lokalnie (http://localhost:1234)
  5. Pollinations.ai — darmowe API, brak klucza

Użycie:
  python pracownik4.py --szukaj-ai
  python pracownik4.py --test "pytanie"
  python pracownik4.py --status

Import w innych skryptach:
  from pracownik4 import szukaj_providera
  provider = szukaj_providera()
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config.json"
LOG_FILE = BASE_DIR / "pracownik4.log"
SEPARATOR = "=" * 60


def log(msg, symbol="•"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {symbol} {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def log_ok(msg):   log(msg, "✓")
def log_err(msg):  log(msg, "✗")
def log_warn(msg): log(msg, "!")
def log_info(msg): log(msg, "→")


def diagnozuj():
    wyniki = {
        "config_istnieje": False, "api_key": "",
        "api_key_env": "", "groq_key_env": "", "hf_token_env": "",
        "openai_zainstalowany": False, "requests_zainstalowany": False,
    }
    if CONFIG_FILE.exists():
        wyniki["config_istnieje"] = True
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            wyniki["api_key"] = cfg.get("api_key", "")
        except Exception:
            pass
    wyniki["api_key_env"] = os.environ.get("OPENAI_API_KEY", "")
    wyniki["groq_key_env"] = os.environ.get("GROQ_API_KEY", "")
    wyniki["hf_token_env"] = os.environ.get("HF_TOKEN", "")
    try:
        import openai; wyniki["openai_zainstalowany"] = True
    except ImportError: pass
    try:
        import requests; wyniki["requests_zainstalowany"] = True
    except ImportError: pass
    return wyniki


def pokaz_diagnozę(d):
    print(f"\n{SEPARATOR}")
    print("  DIAGNOSTYKA ŚRODOWISKA AI")
    print(SEPARATOR)
    print(f"  config.json:          {'TAK' if d['config_istnieje'] else 'BRAK'}")
    print(f"  OPENAI_API_KEY env:   {'[USTAWIONY]' if d['api_key_env'] else '[BRAK]'}")
    print(f"  GROQ_API_KEY env:     {'[USTAWIONY]' if d['groq_key_env'] else '[BRAK]'}")
    print(f"  openai (pip):         {'TAK' if d['openai_zainstalowany'] else 'BRAK'}")
    print(f"  requests (pip):       {'TAK' if d['requests_zainstalowany'] else 'BRAK'}")
    print(SEPARATOR)


TEST_PYTANIE = "Powiedz 'OK' po polsku jednym słowem."


def _chat_request_openai_compat(base_url, api_key, model, pytanie, timeout=10):
    try:
        import requests as req
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {"model": model, "messages": [{"role": "user", "content": pytanie}],
                   "max_tokens": 50, "temperature": 0.1}
        r = req.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def testuj_openai_env(pytanie=TEST_PYTANIE):
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return {"ok": False, "provider": "openai-env", "powod": "brak OPENAI_API_KEY w env"}
    odp = _chat_request_openai_compat("https://api.openai.com/v1", key, "gpt-4o-mini", pytanie)
    if odp:
        return {"ok": True, "provider": "openai-env", "odpowiedz": odp,
                "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "key": key}
    return {"ok": False, "provider": "openai-env", "powod": "błąd API"}


def testuj_groq(pytanie=TEST_PYTANIE):
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return {"ok": False, "provider": "groq", "powod": "brak GROQ_API_KEY w env"}
    odp = _chat_request_openai_compat("https://api.groq.com/openai/v1", key, "llama-3.1-8b-instant", pytanie)
    if odp:
        return {"ok": True, "provider": "groq", "odpowiedz": odp,
                "base_url": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant", "key": key}
    return {"ok": False, "provider": "groq", "powod": "błąd API Groq"}


def testuj_ollama(pytanie=TEST_PYTANIE):
    try:
        import requests as req
        r = req.get("http://localhost:11434/api/tags", timeout=3)
        r.raise_for_status()
        modele = r.json().get("models", [])
        if not modele:
            return {"ok": False, "provider": "ollama", "powod": "brak modeli. Uruchom: ollama pull llama3.2"}
        model_name = modele[0]["name"]
        r2 = req.post("http://localhost:11434/api/chat",
                      json={"model": model_name, "messages": [{"role": "user", "content": pytanie}], "stream": False},
                      timeout=30)
        r2.raise_for_status()
        odp = r2.json()["message"]["content"].strip()
        return {"ok": True, "provider": "ollama", "odpowiedz": odp,
                "base_url": "http://localhost:11434/v1", "model": model_name, "key": "ollama"}
    except Exception as e:
        return {"ok": False, "provider": "ollama", "powod": f"niedostępna: {type(e).__name__}"}


def testuj_lm_studio(pytanie=TEST_PYTANIE):
    odp = _chat_request_openai_compat("http://localhost:1234/v1", "lm-studio", "local-model", pytanie, timeout=7)
    if odp:
        return {"ok": True, "provider": "lm-studio", "odpowiedz": odp,
                "base_url": "http://localhost:1234/v1", "model": "local-model", "key": "lm-studio"}
    return {"ok": False, "provider": "lm-studio", "powod": "niedostępne na localhost:1234"}


def testuj_pollinations(pytanie=TEST_PYTANIE):
    try:
        import requests as req
        import urllib.parse
        r = req.get(f"https://text.pollinations.ai/{urllib.parse.quote(pytanie)}",
                    timeout=20, headers={"Accept": "text/plain"})
        r.raise_for_status()
        odp = r.text.strip()
        if odp:
            return {"ok": True, "provider": "pollinations", "odpowiedz": odp,
                    "base_url": "pollinations", "model": "openai", "key": ""}
        return {"ok": False, "provider": "pollinations", "powod": "pusta odpowiedź"}
    except Exception as e:
        return {"ok": False, "provider": "pollinations", "powod": f"{type(e).__name__}: {e}"}


def szukaj_providera(verbose=True):
    """Testuje wszystkich providerów, zwraca pierwszy działający lub None."""
    if verbose:
        print(f"\n{SEPARATOR}")
        print("  SZUKAM DZIAŁAJĄCEGO AI BACKENDU")
        print(SEPARATOR)
    testy = [
        ("OpenAI (env var)", testuj_openai_env),
        ("Groq (darmowy, env var)", testuj_groq),
        ("Ollama (lokalnie)", testuj_ollama),
        ("LM Studio (lokalnie)", testuj_lm_studio),
        ("Pollinations.ai (bezklucz)", testuj_pollinations),
    ]
    for nazwa, funkcja in testy:
        if verbose: log_info(f"Testuję: {nazwa}...")
        wynik = funkcja()
        if wynik["ok"]:
            log_ok(f"ZNALEZIONO! Provider: {wynik['provider']} → {wynik['odpowiedz']}")
            return wynik
        else:
            if verbose: log_err(f"  {wynik['provider']}: {wynik.get('powod', 'brak odpowiedzi')}")
    if verbose:
        print(f"\n{SEPARATOR}")
        log_warn("Żaden provider nie odpowiedział.")
        print("  1. Ollama: https://ollama.com  →  ollama pull llama3.2")
        print("  2. Groq (darmowy): https://console.groq.com  →  set GROQ_API_KEY=gsk_...")
        print(SEPARATOR)
    return None


def pokaz_raport(provider_info):
    print(f"\n{SEPARATOR}")
    print("  RAPORT PRACOWNIK4 — FINDER AI")
    print(SEPARATOR)
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if provider_info:
        print(f"\n  STATUS: ✓ AI DZIAŁA")
        print(f"  Provider: {provider_info['provider']}")
        print(f"  Model:    {provider_info.get('model', 'auto')}")
        print(f"  Odpowiedź testowa: {provider_info.get('odpowiedz', '?')}")
    else:
        print(f"\n  STATUS: ✗ AI NIEDOSTĘPNE")
        print("  Zainstaluj Ollama lub ustaw GROQ_API_KEY")
    print(SEPARATOR)


def main():
    parser = argparse.ArgumentParser(description="pracownik4.py — Finder AI")
    parser.add_argument("--szukaj-ai", action="store_true", help="Szuka dostępnych AI backendów")
    parser.add_argument("--test", metavar="PYTANIE", help="Testuje AI jednym pytaniem")
    parser.add_argument("--status", action="store_true", help="Tylko diagnostyka środowiska")
    args = parser.parse_args()

    print(f"\n{'#'*60}\n  PRACOWNIK4 — Finder AI\n{'#'*60}")
    log(f"Uruchomiono: {' '.join(sys.argv[1:]) or '(bez flag)'}")

    if args.status:
        pokaz_diagnozę(diagnozuj())
        return

    if args.test:
        log_info(f"Tryb testowy: '{args.test}'")
        provider = szukaj_providera(verbose=True)
        if provider:
            if provider["provider"] == "pollinations":
                import requests, urllib.parse
                r = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote(args.test)}", timeout=30)
                print(f"\nOdpowiedź AI: {r.text.strip()}")
            else:
                odp = _chat_request_openai_compat(provider["base_url"], provider["key"], provider["model"], args.test)
                print(f"\nOdpowiedź AI: {odp}")
        else:
            print("\nBrak działającego AI backendu.")
        return

    pokaz_diagnozę(diagnozuj())
    provider = szukaj_providera(verbose=True)
    pokaz_raport(provider)
    log(f"Koniec. Wynik: {'SUKCES' if provider else 'BRAK AI'}")


if __name__ == "__main__":
    main()
