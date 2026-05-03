"""
pracownik4.py — OSTATNI PRACOWNIK: Naprawa AI dla NeoChat
==========================================================
Diagnozuje problem z AI, szuka działającego backendu (bez płatnego klucza)
i łata neochat.py żeby działał ponownie.

Strategie (kolejność prób):
  1. Zmienna środowiskowa OPENAI_API_KEY lub GROQ_API_KEY
  2. Ollama lokalnie (http://localhost:11434) — darmowy LLM na własnym PC
  3. LM Studio lokalnie (http://localhost:1234) — darmowy LLM na własnym PC
  4. Pollinations.ai — darmowe API, brak klucza (fallback HTTP)
  5. Patch neochat.py — podmiana wyslij_do_ai na wieloproviderową

Użycie:
  python pracownik4.py --szukaj-ai       # szuka i testuje providery
  python pracownik4.py --napraw          # łata neochat.py + config.json
  python pracownik4.py --test "pytanie"  # testuje AI jednym pytaniem
  python pracownik4.py                   # robi wszystko automatycznie
"""

import sys
import os
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ── Ścieżki ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
NEOCHAT_FILE = BASE_DIR / "neochat.py"
NEOCHAT_BACKUP = BASE_DIR / "neochat.py.backup"
LOG_FILE = BASE_DIR / "pracownik4.log"
PATCH_FILE = BASE_DIR / "ai_backend.py"

SEPARATOR = "=" * 60


def log(msg: str, symbol: str = "•"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {symbol} {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_ok(msg: str):   log(msg, "✓")
def log_err(msg: str):  log(msg, "✗")
def log_warn(msg: str): log(msg, "!")
def log_info(msg: str): log(msg, "→")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DIAGNOSTYKA
# ═══════════════════════════════════════════════════════════════════════════════

def diagnozuj() -> dict:
    """Zbiera informacje o stanie NeoChat i AI."""
    wyniki = {
        "config_istnieje": False,
        "api_key": "",
        "api_key_env": "",
        "groq_key_env": "",
        "hf_token_env": "",
        "neochat_istnieje": False,
        "openai_zainstalowany": False,
        "requests_zainstalowany": False,
    }

    # Config
    if CONFIG_FILE.exists():
        wyniki["config_istnieje"] = True
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            wyniki["api_key"] = cfg.get("api_key", "")
        except Exception:
            pass

    # Env vars
    wyniki["api_key_env"] = os.environ.get("OPENAI_API_KEY", "")
    wyniki["groq_key_env"] = os.environ.get("GROQ_API_KEY", "")
    wyniki["hf_token_env"] = os.environ.get("HF_TOKEN", "")

    # neochat.py
    wyniki["neochat_istnieje"] = NEOCHAT_FILE.exists()

    # Pakiety
    try:
        import openai  # noqa
        wyniki["openai_zainstalowany"] = True
    except ImportError:
        pass

    try:
        import requests  # noqa
        wyniki["requests_zainstalowany"] = True
    except ImportError:
        pass

    return wyniki


def pokaz_diagnozę(d: dict):
    print(f"\n{SEPARATOR}")
    print("  DIAGNOSTYKA NEOCHAT / AI")
    print(SEPARATOR)
    print(f"  config.json:          {'TAK' if d['config_istnieje'] else 'BRAK'}")
    print(f"  api_key w config:     {'[PUSTY]' if not d['api_key'] else '[USTAWIONY]'}")
    print(f"  OPENAI_API_KEY env:   {'[USTAWIONY]' if d['api_key_env'] else '[BRAK]'}")
    print(f"  GROQ_API_KEY env:     {'[USTAWIONY]' if d['groq_key_env'] else '[BRAK]'}")
    print(f"  HF_TOKEN env:         {'[USTAWIONY]' if d['hf_token_env'] else '[BRAK]'}")
    print(f"  neochat.py:           {'TAK' if d['neochat_istnieje'] else 'BRAK'}")
    print(f"  openai (pip):         {'TAK' if d['openai_zainstalowany'] else 'BRAK'}")
    print(f"  requests (pip):       {'TAK' if d['requests_zainstalowany'] else 'BRAK'}")
    print(SEPARATOR)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TESTOWANIE PROVIDERÓW
# ═══════════════════════════════════════════════════════════════════════════════

TEST_PYTANIE = "Powiedz 'OK' po polsku jednym słowem."

def _chat_request_openai_compat(base_url: str, api_key: str, model: str,
                                 pytanie: str, timeout: int = 10) -> str | None:
    """Wysyła zapytanie do API kompatybilnego z OpenAI."""
    try:
        import requests as req
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": pytanie}],
            "max_tokens": 50,
            "temperature": 0.1
        }
        r = req.post(
            f"{base_url}/chat/completions",
            headers=headers, json=payload, timeout=timeout
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return None


def testuj_openai_env(pytanie: str = TEST_PYTANIE) -> dict:
    """Próba użycia OPENAI_API_KEY z env."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return {"ok": False, "provider": "openai-env", "powod": "brak OPENAI_API_KEY w env"}
    odp = _chat_request_openai_compat(
        "https://api.openai.com/v1", key, "gpt-4o-mini", pytanie
    )
    if odp:
        return {"ok": True, "provider": "openai-env", "odpowiedz": odp,
                "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "key": key}
    return {"ok": False, "provider": "openai-env", "powod": "błąd API (nieprawidłowy klucz?)"}


def testuj_groq(pytanie: str = TEST_PYTANIE) -> dict:
    """Próba użycia Groq (darmowe API, klucz z env)."""
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return {"ok": False, "provider": "groq", "powod": "brak GROQ_API_KEY w env"}
    odp = _chat_request_openai_compat(
        "https://api.groq.com/openai/v1", key, "llama-3.1-8b-instant", pytanie
    )
    if odp:
        return {"ok": True, "provider": "groq", "odpowiedz": odp,
                "base_url": "https://api.groq.com/openai/v1",
                "model": "llama-3.1-8b-instant", "key": key}
    return {"ok": False, "provider": "groq", "powod": "błąd API Groq"}


def testuj_ollama(pytanie: str = TEST_PYTANIE) -> dict:
    """Próba połączenia z Ollama lokalnie."""
    try:
        import requests as req
        # Sprawdź czy Ollama działa
        r = req.get("http://localhost:11434/api/tags", timeout=3)
        r.raise_for_status()
        modele = r.json().get("models", [])
        if not modele:
            return {"ok": False, "provider": "ollama",
                    "powod": "Ollama działa, ale brak zainstalowanych modeli. "
                             "Uruchom: ollama pull llama3.2"}
        # Weź pierwszy dostępny model
        model_name = modele[0]["name"]
        # Wyślij testoze pytanie
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": pytanie}],
            "stream": False
        }
        r2 = req.post("http://localhost:11434/api/chat",
                      json=payload, timeout=30)
        r2.raise_for_status()
        odp = r2.json()["message"]["content"].strip()
        return {"ok": True, "provider": "ollama", "odpowiedz": odp,
                "base_url": "http://localhost:11434/v1",
                "model": model_name, "key": "ollama"}
    except Exception as e:
        return {"ok": False, "provider": "ollama",
                "powod": f"Ollama niedostępna: {type(e).__name__}. "
                         "Zainstaluj z: https://ollama.com"}


def testuj_lm_studio(pytanie: str = TEST_PYTANIE) -> dict:
    """Próba połączenia z LM Studio (localhost:1234)."""
    odp = _chat_request_openai_compat(
        "http://localhost:1234/v1", "lm-studio", "local-model", pytanie, timeout=5
    )
    if odp:
        return {"ok": True, "provider": "lm-studio", "odpowiedz": odp,
                "base_url": "http://localhost:1234/v1",
                "model": "local-model", "key": "lm-studio"}
    return {"ok": False, "provider": "lm-studio",
            "powod": "LM Studio niedostępne na localhost:1234"}


def testuj_pollinations(pytanie: str = TEST_PYTANIE) -> dict:
    """Pollinations.ai — darmowe API bez klucza."""
    try:
        import requests as req
        import urllib.parse
        encoded = urllib.parse.quote(pytanie)
        r = req.get(
            f"https://text.pollinations.ai/{encoded}",
            timeout=20,
            headers={"Accept": "text/plain"}
        )
        r.raise_for_status()
        odp = r.text.strip()
        if odp:
            return {"ok": True, "provider": "pollinations", "odpowiedz": odp,
                    "base_url": "pollinations", "model": "openai", "key": ""}
        return {"ok": False, "provider": "pollinations", "powod": "pusta odpowiedź"}
    except Exception as e:
        return {"ok": False, "provider": "pollinations",
                "powod": f"Błąd: {type(e).__name__}: {e}"}


def szukaj_providera(verbose: bool = True) -> dict | None:
    """Testuje wszystkich providerów, zwraca pierwszy działający."""
    if verbose:
        print(f"\n{SEPARATOR}")
        print("  SZUKAM DZIAŁAJĄCEGO AI BACKENDU")
        print(SEPARATOR)

    testy = [
        ("OpenAI (env var)", testuj_openai_env),
        ("Groq (env var + darmowy)", testuj_groq),
        ("Ollama (lokalnie)", testuj_ollama),
        ("LM Studio (lokalnie)", testuj_lm_studio),
        ("Pollinations.ai (bezklucz)", testuj_pollinations),
    ]

    for nazwa, funkcja in testy:
        if verbose:
            log_info(f"Testuję: {nazwa}...")
        wynik = funkcja()
        if wynik["ok"]:
            log_ok(f"ZNALEZIONO! Provider: {wynik['provider']} → {wynik['odpowiedz']}")
            return wynik
        else:
            if verbose:
                log_err(f"  {wynik['provider']}: {wynik.get('powod', 'brak odpowiedzi')}")

    if verbose:
        print(f"\n{SEPARATOR}")
        log_warn("Żaden provider nie odpowiedział.")
        print("  Opcje do rozważenia:")
        print("  1. Zainstaluj Ollama: https://ollama.com")
        print("     ollama pull llama3.2")
        print("  2. Darmowy klucz Groq: https://console.groq.com")
        print("     ustaw: set GROQ_API_KEY=gsk_...")
        print("  3. Darmowy klucz OpenAI: https://platform.openai.com")
        print("     ustaw: set OPENAI_API_KEY=sk-...")
        print(SEPARATOR)

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. NAPRAWIANIE — patch neochat.py + config.json
# ═══════════════════════════════════════════════════════════════════════════════

PATCH_BACKEND_CODE = '''"""
ai_backend.py — Wieloproviderowy backend AI dla NeoChat
Generowany automatycznie przez pracownik4.py
"""

import os
import json
from pathlib import Path


def _req_post(url, headers, payload, timeout=30):
    import requests
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def wyslij_openai_compat(base_url: str, api_key: str, model: str,
                          messages: list, max_tokens: int, temperature: float) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    data = _req_post(f"{base_url}/chat/completions", headers, payload)
    return data["choices"][0]["message"]["content"].strip()


def wyslij_pollinations(messages: list, **kwargs) -> str:
    import requests
    import urllib.parse
    # Weź ostatnią wiadomość użytkownika
    pytanie = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"),
        "Cześć"
    )
    encoded = urllib.parse.quote(pytanie)
    r = requests.get(
        f"https://text.pollinations.ai/{encoded}",
        timeout=30,
        headers={"Accept": "text/plain"}
    )
    r.raise_for_status()
    return r.text.strip()


# ── Auto-wykrycie backendu ─────────────────────────────────────────────────
_BACKEND_CACHE: dict | None = None


def _wykryj_backend() -> dict:
    global _BACKEND_CACHE
    if _BACKEND_CACHE is not None:
        return _BACKEND_CACHE

    # 1. Plik z zapisanym backendem
    backend_file = Path(__file__).parent / ".ai_backend_cache.json"
    if backend_file.exists():
        try:
            cached = json.loads(backend_file.read_text(encoding="utf-8"))
            _BACKEND_CACHE = cached
            return cached
        except Exception:
            pass

    # 2. Env vars
    for key_env, base_url, model, provider in [
        ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini", "openai"),
        ("GROQ_API_KEY", "https://api.groq.com/openai/v1", "llama-3.1-8b-instant", "groq"),
    ]:
        k = os.environ.get(key_env, "")
        if k:
            _BACKEND_CACHE = {"provider": provider, "base_url": base_url,
                               "model": model, "key": k}
            return _BACKEND_CACHE

    # 3. Ollama lokalnie
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        modele = r.json().get("models", [])
        if modele:
            _BACKEND_CACHE = {"provider": "ollama",
                               "base_url": "http://localhost:11434/v1",
                               "model": modele[0]["name"], "key": "ollama"}
            return _BACKEND_CACHE
    except Exception:
        pass

    # 4. LM Studio
    try:
        import requests
        requests.get("http://localhost:1234/v1/models", timeout=2).raise_for_status()
        _BACKEND_CACHE = {"provider": "lm-studio",
                           "base_url": "http://localhost:1234/v1",
                           "model": "local-model", "key": "lm-studio"}
        return _BACKEND_CACHE
    except Exception:
        pass

    # 5. Pollinations (zawsze dostępne)
    _BACKEND_CACHE = {"provider": "pollinations",
                       "base_url": "pollinations", "model": "", "key": ""}
    return _BACKEND_CACHE


def wyslij_do_ai_multi(messages: list, cfg: dict) -> str:
    """Zamiennik dla wyslij_do_ai() z neochat.py — używa najlepszego dostępnego backendu."""
    backend = _wykryj_backend()
    provider = backend["provider"]

    if provider == "pollinations":
        return wyslij_pollinations(messages)

    return wyslij_openai_compat(
        base_url=backend["base_url"],
        api_key=backend["key"],
        model=cfg.get("model", backend["model"]) if provider not in ("ollama", "lm-studio")
              else backend["model"],
        messages=messages,
        max_tokens=cfg.get("max_tokens", 1000),
        temperature=cfg.get("temperature", 0.7)
    )
'''


def zapisz_plik_backendu():
    """Tworzy ai_backend.py w folderze NeoChat."""
    PATCH_FILE.write_text(PATCH_BACKEND_CODE, encoding="utf-8")
    log_ok(f"Zapisano backend: {PATCH_FILE}")


def zapisz_backend_cache(provider_info: dict):
    """Zapamiętuje działający backend w pliku cache."""
    cache_file = BASE_DIR / ".ai_backend_cache.json"
    cache_file.write_text(json.dumps(provider_info, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    log_ok(f"Backend cache zapisany: {cache_file.name}")


def patch_neochat():
    """Łata neochat.py żeby używało ai_backend.py zamiast bezpośrednio OpenAI."""
    if not NEOCHAT_FILE.exists():
        log_err("neochat.py nie istnieje — pomijam patch")
        return False

    tekst = NEOCHAT_FILE.read_text(encoding="utf-8")

    # Sprawdź czy już spatchowane
    if "ai_backend" in tekst:
        log_ok("neochat.py już zawiera patch ai_backend — OK")
        return True

    # Backup
    shutil.copy2(NEOCHAT_FILE, NEOCHAT_BACKUP)
    log_info(f"Backup: {NEOCHAT_BACKUP.name}")

    # Dodaj import ai_backend na początku
    stary_import = "from openai import OpenAI"
    if stary_import not in tekst:
        log_warn("Nie znaleziono standardowego importu openai — pomijam automatyczny patch")
        log_info("Możesz ręcznie zastąpić wyslij_do_ai() w neochat.py wywołaniem ai_backend.wyslij_do_ai_multi()")
        return False

    # Wstaw import ai_backend po liniach importów
    nowy_blok = """
# ── AI Backend (patch przez pracownik4.py) ──────────────────────────────────
try:
    from ai_backend import wyslij_do_ai_multi as _wyslij_do_ai_multi
    _MULTI_BACKEND = True
except ImportError:
    _MULTI_BACKEND = False
"""

    # Wstaw po ostatnim imporcie (szukamy def wyslij_do_ai)
    stara_funkcja = "def wyslij_do_ai(messages: list, cfg: dict) -> str:"
    nowa_funkcja = """def wyslij_do_ai(messages: list, cfg: dict) -> str:
    \"\"\"Wysyła wiadomości do AI — wieloproviderowy wrapper (patch pracownik4).\"\"\"
    if _MULTI_BACKEND:
        return _wyslij_do_ai_multi(messages, cfg)
    # Oryginalna logika OpenAI (fallback):"""

    if stara_funkcja not in tekst:
        log_warn("Nie znaleziono def wyslij_do_ai — pomijam patch funkcji")
        return False

    # Wstaw blok importu przed wyslij_do_ai
    tekst = tekst.replace(
        "# ── Klient OpenAI",
        nowy_blok + "\n# ── Klient OpenAI"
    )

    # Zamień nagłówek funkcji
    tekst = tekst.replace(stara_funkcja,
                           nowa_funkcja, 1)

    # Wciągnij starą treść funkcji (dodaj indent przez dodanie 4 spacji do starego kodu)
    # Zamiast pełnego parsowania — po prostu sprawdź że nagłówek się zmienił
    NEOCHAT_FILE.write_text(tekst, encoding="utf-8")
    log_ok("neochat.py spatchowany — używa teraz ai_backend.py")
    return True


def napraw_config(provider_info: dict):
    """Aktualizuje config.json żeby wskazywał na działający backend."""
    try:
        if CONFIG_FILE.exists():
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        else:
            cfg = {}

        # Zaktualizuj model jeśli provider nie jest OpenAI
        if provider_info["provider"] in ("groq", "ollama", "lm-studio", "pollinations"):
            cfg["model"] = provider_info.get("model", cfg.get("model", "llama-3.1-8b-instant"))
            cfg["_ai_provider"] = provider_info["provider"]
            cfg["_ai_base_url"] = provider_info.get("base_url", "")

        # Zapisz klucz jeśli dostępny (nie Pollinations/Ollama)
        if provider_info.get("key") and provider_info["key"] not in ("ollama", "lm-studio", ""):
            cfg["api_key"] = provider_info["key"]

        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        log_ok(f"config.json zaktualizowany (provider: {provider_info['provider']})")
    except Exception as e:
        log_err(f"Błąd aktualizacji config: {e}")


def stworz_env_file(provider_info: dict):
    """Tworzy .env z odpowiednimi zmiennymi jeśli trzeba."""
    env_file = BASE_DIR / ".env"
    linie = []
    if env_file.exists():
        linie = env_file.read_text(encoding="utf-8").splitlines()

    def ustaw_zmienna(linie, key, value):
        for i, l in enumerate(linie):
            if l.startswith(f"{key}="):
                linie[i] = f"{key}={value}"
                return linie
        linie.append(f"{key}={value}")
        return linie

    provider = provider_info["provider"]
    if provider == "openai" and provider_info.get("key"):
        linie = ustaw_zmienna(linie, "OPENAI_API_KEY", provider_info["key"])
    elif provider == "groq" and provider_info.get("key"):
        linie = ustaw_zmienna(linie, "GROQ_API_KEY", provider_info["key"])

    if linie:
        env_file.write_text("\n".join(linie) + "\n", encoding="utf-8")
        log_ok(f".env zaktualizowany: {env_file}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PODSUMOWANIE
# ═══════════════════════════════════════════════════════════════════════════════

def pokaz_raport(provider_info: dict | None, diag: dict):
    print(f"\n{SEPARATOR}")
    print("  RAPORT PRACOWNIK4 — NAPRAWA AI")
    print(SEPARATOR)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Data: {ts}")
    print(f"  Plik logu: {LOG_FILE}")

    if provider_info:
        print(f"\n  STATUS: ✓ AI DZIAŁA")
        print(f"  Provider:   {provider_info['provider']}")
        print(f"  Model:      {provider_info.get('model', 'auto')}")
        base_url = provider_info.get('base_url', '')
        if base_url not in ('pollinations', ''):
            print(f"  Base URL:   {base_url}")
        print(f"\n  Odpowiedź testowa: {provider_info.get('odpowiedz', '?')}")
        print()
        print("  Co zostało zrobione:")
        print("  ✓ ai_backend.py — nowy wieloproviderowy backend")
        print("  ✓ neochat.py    — spatchowany (używa ai_backend)")
        print("  ✓ config.json   — zaktualizowany")
        if provider_info["provider"] == "pollinations":
            print()
            print("  UWAGA: Używasz Pollinations.ai (darmowy, bez klucza).")
            print("  Dla lepszej jakości AI zainstaluj Ollama:")
            print("    https://ollama.com → ollama pull llama3.2")
    else:
        print(f"\n  STATUS: ✗ AI NIEDOSTĘPNE")
        print()
        print("  Co możesz zrobić:")
        print()
        print("  OPCJA A — Ollama (lokalne AI, w pełni offline):")
        print("    1. Pobierz: https://ollama.com/download")
        print("    2. Zainstaluj i uruchom")
        print("    3. Uruchom: ollama pull llama3.2")
        print("    4. Uruchom ponownie: python pracownik4.py")
        print()
        print("  OPCJA B — Groq (darmowy, szybki, w chmurze):")
        print("    1. Zarejestruj się: https://console.groq.com")
        print("    2. Stwórz darmowy klucz API")
        print("    3. Ustaw: set GROQ_API_KEY=gsk_twoj_klucz")
        print("    4. Uruchom ponownie: python pracownik4.py")
        print()
        print("  OPCJA C — OpenAI (płatne):")
        print("    1. https://platform.openai.com/api-keys")
        print("    2. set OPENAI_API_KEY=sk-twoj_klucz")

    print(SEPARATOR)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="pracownik4.py — Naprawa AI dla NeoChat"
    )
    parser.add_argument("--szukaj-ai", action="store_true",
                        help="Szuka i testuje dostępne AI backendy")
    parser.add_argument("--napraw", action="store_true",
                        help="Naprawia neochat.py i config.json")
    parser.add_argument("--test", metavar="PYTANIE",
                        help="Testuje AI jednym pytaniem")
    parser.add_argument("--status", action="store_true",
                        help="Pokazuje tylko diagnostykę")
    args = parser.parse_args()

    print(f"\n{'#' * 60}")
    print("  PRACOWNIK4 — Ostatni Pracownik: Naprawa AI")
    print(f"{'#' * 60}")
    log(f"Uruchomiono: {' '.join(sys.argv[1:]) or '(bez flag — auto)'}")

    diag = diagnozuj()

    if args.status:
        pokaz_diagnozę(diag)
        return

    # Tryb testowy — jedno pytanie
    if args.test:
        log_info(f"Tryb testowy: '{args.test}'")
        provider = szukaj_providera(verbose=True)
        if provider:
            if provider["provider"] == "pollinations":
                import requests, urllib.parse
                r = requests.get(
                    f"https://text.pollinations.ai/{urllib.parse.quote(args.test)}",
                    timeout=30
                )
                print(f"\nOdpowiedź AI: {r.text.strip()}")
            else:
                odp = _chat_request_openai_compat(
                    provider["base_url"], provider["key"],
                    provider["model"], args.test
                )
                print(f"\nOdpowiedź AI: {odp}")
        return

    # Domyślny tryb — pełne szukanie + naprawa
    pokaz_diagnozę(diag)

    log_info("Szukam działającego AI backendu...")
    provider = szukaj_providera(verbose=True)

    # Zawsze twórz plik backendu
    log_info("Tworzę ai_backend.py...")
    zapisz_plik_backendu()

    if provider:
        zapisz_backend_cache(provider)
        napraw_config(provider)
        stworz_env_file(provider)

    # Patch neochat.py
    if not args.szukaj_ai:
        log_info("Patczuję neochat.py...")
        patch_neochat()

    pokaz_raport(provider, diag)

    log(f"Koniec. Wynik: {'SUKCES' if provider else 'BRAK AI'}")


if __name__ == "__main__":
    main()
