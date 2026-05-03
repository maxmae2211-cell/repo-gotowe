"""
NeoChat — własny asystent AI oparty na OpenAI API
z w pełni konfigurowalną własną moderacją.

Użycie:
  python neochat.py                    # tryb interaktywny (czat)
  python neochat.py "Twoje pytanie"    # jednorazowe pytanie
  python neochat.py --set-key sk-...   # zapisz klucz API
  python neochat.py --show-config      # pokaż konfigurację
"""

import sys
import os
import json
import argparse
from pathlib import Path

try:
    from moderacja import sprawdz_wejscie, sprawdz_wyjscie
except ImportError:
    def sprawdz_wejscie(tekst): return None
    def sprawdz_wyjscie(tekst): return tekst

# ── Ścieżki ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
ENV_FILE = BASE_DIR / ".env"

# ── Konfiguracja domyślna ────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "api_key": "",
    "model": "gpt-4o-mini",
    "system_prompt": "Jesteś pomocnym asystentem o nazwie NeoChat.",
    "max_tokens": 1000,
    "temperature": 0.7,
    "history_limit": 10   # ile ostatnich wiadomości trzymać w kontekście
}


# ── Środowisko lokalne ──────────────────────────────────────────────────────
def load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# ── Zarządzanie konfiguracją ─────────────────────────────────────────────────
def load_config() -> dict:
    load_env_file()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # uzupełnij brakujące klucze wartościami domyślnymi
        for k, v in DEFAULT_CONFIG.items():
            if k not in data:
                data[k] = v
        return data
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def run_setup() -> None:
    cfg = load_config()

    print("NeoChat setup")
    print("Pozostaw puste i naciśnij Enter, aby zachować obecną wartość.\n")

    api_key = input("OpenAI API key: ").strip()
    model = input(f"Model [{cfg['model']}]: ").strip()
    system_prompt = input(f"System prompt [{cfg['system_prompt']}]: ").strip()

    if api_key:
        cfg["api_key"] = api_key
    if model:
        cfg["model"] = model
    if system_prompt:
        cfg["system_prompt"] = system_prompt

    save_config(cfg)
    print(f"\n[OK] Konfiguracja zapisana do: {CONFIG_FILE}")



# ── Klient OpenAI ─────────────────────────────────────────────────────────────
def wyslij_do_ai(messages: list, cfg: dict) -> str:
    """Wysyła wiadomości do OpenAI API i zwraca odpowiedź."""
    try:
        from openai import OpenAI
    except ImportError:
        print("[BŁĄD] Zainstaluj bibliotekę: pip install openai")
        sys.exit(1)

    api_key = cfg.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[BŁĄD] Brak klucza API. Ustaw go przez: python neochat.py --set-key sk-...")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=messages,
        max_tokens=cfg["max_tokens"],
        temperature=cfg["temperature"]
    )
    return response.choices[0].message.content.strip()


# ── Główna pętla czatu ────────────────────────────────────────────────────────
def czat(jednorazowe: str | None = None):
    cfg = load_config()

    historia: list[dict] = [
        {"role": "system", "content": cfg["system_prompt"]}
    ]

    def odpowiedz(tekst_uzytkownika: str) -> str:
        blokada = sprawdz_wejscie(tekst_uzytkownika)
        if blokada:
            return f"[MODERACJA] {blokada}"

        historia.append({"role": "user", "content": tekst_uzytkownika})

        # Ogranicz historię (system + ostatnie N wiadomości)
        limit = cfg["history_limit"] * 2  # user + assistant pary
        if len(historia) > limit + 1:
            del historia[1:len(historia) - limit]

        odp = wyslij_do_ai(historia, cfg)
        odp = sprawdz_wyjscie(odp)
        historia.append({"role": "assistant", "content": odp})
        return odp

    if jednorazowe:
        print(odpowiedz(jednorazowe))
        return

    # Tryb interaktywny
    print("=" * 50)
    print("  NeoChat — wpisz 'exit' lub Ctrl+C aby wyjść")
    print("=" * 50)
    while True:
        try:
            tekst = input("\nTy: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nDo widzenia!")
            break
        if not tekst:
            continue
        if tekst.lower() in ("exit", "quit", "wyjdź", "koniec"):
            print("Do widzenia!")
            break
        odp = odpowiedz(tekst)
        print(f"\nNeoChat: {odp}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="NeoChat — własny asystent AI z własną moderacją"
    )
    parser.add_argument("pytanie", nargs="?", help="Jednorazowe pytanie do AI")
    parser.add_argument("--set-key", metavar="KLUCZ", help="Zapisz klucz OpenAI API")
    parser.add_argument("--set-model", metavar="MODEL", help="Ustaw model (np. gpt-4o)")
    parser.add_argument("--set-prompt", metavar="PROMPT", help="Ustaw system prompt")
    parser.add_argument("--setup", action="store_true", help="Interaktywnie skonfiguruj NeoChat")
    parser.add_argument("--show-config", action="store_true", help="Pokaż aktualną konfigurację")

    args = parser.parse_args()

    if args.setup:
        run_setup()
        return

    if args.set_key:
        cfg = load_config()
        cfg["api_key"] = args.set_key.strip()
        save_config(cfg)
        print(f"[OK] Klucz API zapisany do: {CONFIG_FILE}")
        return

    if args.set_model:
        cfg = load_config()
        cfg["model"] = args.set_model.strip()
        save_config(cfg)
        print(f"[OK] Model ustawiony na: {cfg['model']}")
        return

    if args.set_prompt:
        cfg = load_config()
        cfg["system_prompt"] = args.set_prompt.strip()
        save_config(cfg)
        print(f"[OK] System prompt zaktualizowany.")
        return

    if args.show_config:
        cfg = load_config()
        masked = dict(cfg)
        if masked.get("api_key"):
            k = masked["api_key"]
            masked["api_key"] = k[:8] + "..." + k[-4:] if len(k) > 12 else "***"
        print(json.dumps(masked, ensure_ascii=False, indent=2))
        return

    czat(jednorazowe=args.pytanie)


if __name__ == "__main__":
    main()
