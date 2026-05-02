"""
Minimalny entrypoint agenta HTTP dla AI Toolkit Agent Inspector.
Uruchomienie lokalne:
  python -m debugpy --listen 127.0.0.1:5679 -m agentdev run src/agent.py --verbose --port 8088 -- --server
Albo przez VS Code: "Agent Inspector: Debug HTTP Server" w launch.json
"""
import argparse


def run_cli() -> None:
    print("Agent uruchomiony w trybie CLI. Wpisz zapytanie lub Ctrl+C aby zakończyć.")
    while True:
        try:
            user_input = input(">> ")
            if not user_input.strip():
                continue
            # Tu podłącz właściwą logikę agenta
            print(f"[agent] odpowiedź na: {user_input!r}")
        except (KeyboardInterrupt, EOFError):
            break


def run_server(port: int = 8088) -> None:
    try:
        from fastapi import FastAPI
        import uvicorn

        app = FastAPI(title="Agent HTTP Server")

        @app.get("/health")
        def health():
            return {"status": "ok"}

        @app.post("/run")
        def run(body: dict):
            # Tu podłącz właściwą logikę agenta
            return {"response": f"Odebrano: {body}"}

        uvicorn.run(app, host="127.0.0.1", port=port)
    except ImportError as e:
        raise SystemExit(f"Brak zależności serwera: {e}. Zainstaluj fastapi i uvicorn.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent entrypoint")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--server", action="store_true", help="Uruchom serwer HTTP")
    group.add_argument("--cli", action="store_true", help="Uruchom w trybie CLI")
    parser.add_argument("--port", type=int, default=8088, help="Port serwera HTTP (domyślnie 8088)")
    args = parser.parse_args()

    if args.server:
        run_server(args.port)
    else:
        run_cli()


if __name__ == "__main__":
    main()
