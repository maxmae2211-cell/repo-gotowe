"""
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
    import time
    # Weź ostatnią wiadomość użytkownika
    pytanie = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"),
        "Cześć"
    )
    encoded = urllib.parse.quote(pytanie)
    url = f"https://text.pollinations.ai/{encoded}"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=60, headers={"Accept": "text/plain"})
            r.raise_for_status()
            return r.text.strip()
        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except requests.exceptions.RequestException:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise


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
