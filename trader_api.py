#!/usr/bin/env python3
"""FastAPI REST API dla crypto_auto_trader.

Endpointy:
  GET /status   — aktualny stan pozycji tradera
  GET /trades   — historia transakcji z SQLite
  GET /signal   — ostatni sygnał (wymaga aktywnego rynku)
  GET /health   — liveness check

Uruchomienie:
  uvicorn trader_api:app --host 0.0.0.0 --port 8080
"""

import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from crypto_auto_trader import load_config, load_state

CONFIG_PATH = Path("trader_config.json")

app = FastAPI(title="Crypto Trader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _cfg():
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=500, detail="Brak trader_config.json")
    return load_config(CONFIG_PATH)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    cfg = _cfg()
    state = load_state(Path(cfg.state_file))
    return {
        "symbol": cfg.symbol,
        "exchange": cfg.exchange,
        "position_open": state.get("position_open", False),
        "entry_price": state.get("entry_price", 0.0),
        "amount": state.get("amount", 0.0),
        "last_signal": state.get("last_signal", "none"),
        "updated_at": state.get("updated_at", 0),
    }


@app.get("/trades")
def trades(limit: int = 50):
    cfg = _cfg()
    db_path = Path(cfg.db_file)
    if not db_path.exists():
        return {"trades": [], "total": 0}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {
        "trades": [dict(r) for r in rows],
        "total": len(rows),
    }


@app.get("/signal")
def signal():
    import ccxt
    cfg = _cfg()
    try:
        ex = getattr(ccxt, cfg.exchange)({"enableRateLimit": True})
        candles = ex.fetch_ohlcv(
            cfg.symbol, cfg.timeframe,
            limit=cfg.slow_sma + cfg.macd_slow + cfg.macd_signal + 10
        )
        closes = [float(c[4]) for c in candles]
        from crypto_auto_trader import decide_signal, rsi, macd
        sig = decide_signal(closes, cfg)
        try:
            rsi_val = rsi(closes, period=14)
        except ValueError:
            rsi_val = None
        try:
            ml, sl, hist = macd(closes, fast=cfg.macd_fast,
                                slow=cfg.macd_slow, signal=cfg.macd_signal)
        except ValueError:
            ml = sl = hist = None
        return {
            "symbol": cfg.symbol,
            "signal": sig,
            "price": closes[-1],
            "rsi": rsi_val,
            "macd_line": ml,
            "macd_signal": sl,
            "macd_histogram": hist,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
