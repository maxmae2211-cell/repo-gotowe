"""
Entrypoint agenta HTTP dla AI Toolkit Agent Inspector.
Uruchomienie lokalne:
  python -m debugpy --listen 127.0.0.1:5679 -m agentdev run src/agent.py --verbose --port 8088 -- --server
Albo przez VS Code: "Agent Inspector: Debug HTTP Server" w launch.json
"""
import argparse
import subprocess
from pathlib import Path
from typing import Any


# --- Taurus helpers ---

TAURUS_CONFIGS = {
    "api": "test-api.yml",
    "advanced": "test-advanced.yml",
    "locust": "test-locust.yml",
    "support": "test-support.yml",
}

WORKSPACE = Path(__file__).parent.parent


def run_taurus(config: str = "api", mode: str = "standard") -> dict[str, Any]:
    """Uruchamia test Taurus przez run-taurus.ps1."""
    cfg_file = TAURUS_CONFIGS.get(config, config)
    script = WORKSPACE / "scripts" / "run-taurus.ps1"
    if not script.exists():
        return {"error": f"Skrypt {script} nie istnieje."}
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script), "-Mode", mode, "-Config", cfg_file,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(WORKSPACE))
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-3000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout po 300s."}
    except Exception as exc:
        return {"error": str(exc)}


def get_last_results() -> dict[str, Any]:
    """Zwraca skrócone dane z ostatniego artefaktu kpi.jtl."""
    dirs = sorted(WORKSPACE.glob("20*_*"))
    if not dirs:
        return {"error": "Brak artefaktów testowych."}
    latest = dirs[-1]
    kpi = latest / "kpi.jtl"
    if not kpi.exists():
        return {"dir": str(latest), "error": "Brak kpi.jtl"}
    lines = kpi.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
    return {
        "dir": latest.name,
        "requests": max(0, len(lines) - 1),
        "preview": lines[-1] if len(lines) > 1 else "",
    }


# --- CLI mode ---

def run_cli() -> None:  # noqa: C901
    print("Agent Taurus — tryb CLI. Wpisz komendę lub 'help'. Ctrl+C aby wyjść.")
    commands = {
        "help": "Wyświetl dostępne komendy",
        "run [api|advanced|locust|support] [health|standard]": "Uruchom test Taurus",
        "results": "Pokaż ostatnie wyniki",
        "status": "Status środowiska",
    }
    for cmd, desc in commands.items():
        print(f"  {cmd:45} — {desc}")
    print()
    while True:
        try:
            raw = input(">> ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not raw:
            continue
        parts = raw.split()
        if parts[0] == "run":
            cfg = parts[1] if len(parts) > 1 else "api"
            mode = parts[2] if len(parts) > 2 else "standard"
            print(f"Uruchamiam: config={cfg} mode={mode} ...")
            result = run_taurus(cfg, mode)
            print(result)
        elif parts[0] == "results":
            print(get_last_results())
        elif parts[0] == "status":
            import subprocess as sp
            bzt = sp.run(["python", "-m", "bzt", "--version"], capture_output=True, text=True)
            java = sp.run(["java", "-version"], capture_output=True, text=True)
            print(f"bzt: {bzt.stdout or bzt.stderr}".strip())
            print(f"java: {java.stderr or 'niedostępna'}".strip()[:80])
        elif parts[0] == "help":
            for cmd, desc in commands.items():
                print(f"  {cmd:45} — {desc}")
        else:
            print(f"Nieznana komenda: {parts[0]}")


# --- HTTP server mode ---

def run_server(port: int = 8088) -> None:  # pragma: no cover
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        import uvicorn

        app = FastAPI(title="Taurus Agent HTTP Server", version="1.0.0")

        class RunRequest(BaseModel):
            config: str = "api"
            mode: str = "standard"

        @app.get("/health")
        def health():
            return {"status": "ok", "workspace": str(WORKSPACE)}

        @app.get("/results")
        def results():
            return get_last_results()

        @app.post("/run")
        def run(req: RunRequest):
            if req.config not in TAURUS_CONFIGS and not req.config.endswith(".yml"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Nieznana konfiguracja: {req.config}. Dostępne: {list(TAURUS_CONFIGS.keys())}"
                )
            return run_taurus(req.config, req.mode)

        uvicorn.run(app, host="127.0.0.1", port=port)
    except ImportError as e:
        raise SystemExit(f"Brak zależności: {e}. Zainstaluj: pip install fastapi uvicorn pydantic")


# --- Entrypoint ---

def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Taurus Agent entrypoint")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--server", action="store_true", help="Uruchom serwer HTTP")
    group.add_argument("--cli", action="store_true", help="Tryb CLI")
    parser.add_argument("--port", type=int, default=8088, help="Port serwera HTTP (domyślnie 8088)")
    args = parser.parse_args()

    if args.server:
        run_server(args.port)
    else:
        run_cli()


if __name__ == "__main__":
    main()
