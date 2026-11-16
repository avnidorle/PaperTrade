"""PaperTrade API: market data, indicators, signals and a paper-trading engine (FastAPI + SQLite)."""
import hashlib, sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    import yfinance as yf
except ImportError:
    yf = None

SYMBOLS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "ITC"]
BASE = {"RELIANCE": 2900, "TCS": 4100, "INFY": 1850, "HDFCBANK": 1680, "ICICIBANK": 1260, "ITC": 470}
INITIAL = 100_000.0
DB = "papertrade.db"

app = FastAPI(title="PaperTrade API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


# ---------- database ----------
@contextmanager
def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()  # an exception inside the block skips the commit, so orders are atomic
    finally:
        conn.close()


def init_db(initial=INITIAL):
    with db() as c:
        c.executescript(
            """CREATE TABLE IF NOT EXISTS account(id INTEGER PRIMARY KEY, cash REAL, initial REAL);
            CREATE TABLE IF NOT EXISTS holdings(symbol TEXT PRIMARY KEY, qty INTEGER, avg REAL);
            CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, symbol TEXT,
              side TEXT, qty INTEGER, entry REAL, exit REAL, pnl REAL);"""
        )
        c.execute("INSERT OR IGNORE INTO account VALUES(1,?,?)", (initial, initial))


init_db()


# ---------- trading engine ----------
def execute(c, symbol, side, qty, price):
    """Fill an order at `price`. Validates cash/holdings, keeps a weighted average buy price."""
    cash = c.execute("SELECT cash FROM account WHERE id=1").fetchone()["cash"]
    h = c.execute("SELECT qty, avg FROM holdings WHERE symbol=?", (symbol,)).fetchone()
    ts = datetime.now().isoformat(timespec="seconds")
    if side == "BUY":
        cost = qty * price
        if cost > cash:
            raise HTTPException(400, f"Insufficient cash: need ₹{cost:,.2f}, have ₹{cash:,.2f}")
        hq, ha = (h["qty"], h["avg"]) if h else (0, 0.0)
        c.execute("INSERT OR REPLACE INTO holdings VALUES(?,?,?)", (symbol, hq + qty, (hq * ha + cost) / (hq + qty)))
        c.execute("UPDATE account SET cash=cash-? WHERE id=1", (cost,))
        c.execute("INSERT INTO trades(ts,symbol,side,qty,entry) VALUES(?,?,?,?,?)", (ts, symbol, side, qty, price))
        return f"Bought {qty} {symbol} at ₹{price:,.2f}"
    if not h or qty > h["qty"]:
        raise HTTPException(400, f"You hold {h['qty'] if h else 0} {symbol}; cannot sell {qty}")
    pnl = (price - h["avg"]) * qty
    if h["qty"] - qty:
        c.execute("UPDATE holdings SET qty=? WHERE symbol=?", (h["qty"] - qty, symbol))
    else:
        c.execute("DELETE FROM holdings WHERE symbol=?", (symbol,))
    c.execute("UPDATE account SET cash=cash+? WHERE id=1", (qty * price,))
    c.execute("INSERT INTO trades(ts,symbol,side,qty,entry,exit,pnl) VALUES(?,?,?,?,?,?,?)",
              (ts, symbol, side, qty, h["avg"], price, pnl))
    return f"Sold {qty} {symbol} at ₹{price:,.2f}. Realized P&L ₹{pnl:,.2f}"


# ---------- market data + indicators ----------
_cache = {}


def mock(symbol):
    rng = np.random.default_rng(int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16))
    close = BASE[symbol] * np.exp(np.cumsum(rng.normal(0.0003, 0.012, 260)))
    open_ = np.r_[close[0], close[:-1]]
    sp = rng.uniform(0.001, 0.01, 260)
    return pd.DataFrame({"open": open_, "high": np.maximum(open_, close) * (1 + sp),
                         "low": np.minimum(open_, close) * (1 - sp), "close": close,
                         "volume": rng.integers(500_000, 2_000_000, 260)},
                        index=pd.bdate_range(end=datetime.now().date(), periods=260))


def indicators(df):
    df, c = df.copy(), df["close"]
    df["sma20"], df["sma50"] = c.rolling(20).mean(), c.rolling(50).mean()
    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    d = c.diff()
    g = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    df["rsi"] = 100 - 100 / (1 + g / l.replace(0, np.nan))
    df["macd"] = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    sd = c.rolling(20).std(ddof=0)
    df["bb_u"], df["bb_l"] = df["sma20"] + 2 * sd, df["sma20"] - 2 * sd
    return df


def history(symbol):
    hit = _cache.get(symbol)
    if hit and (datetime.now() - hit[0]).total_seconds() < 300:
        return hit[1], hit[2]
    df, src = None, "simulated"
    if yf:
        try:
            d = yf.Ticker(symbol + ".NS").history(period="1y")
            if len(d) > 60:
                df, src = d.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]], "yahoo"
        except Exception:
            pass
    df = indicators(mock(symbol) if df is None else df)
    _cache[symbol] = (datetime.now(), df, src)
    return df, src


def price(s):
    return float(history(s)[0]["close"].iloc[-1])


def check(s):
    if s not in SYMBOLS:
        raise HTTPException(404, "Unknown symbol")


# ---------- routes ----------
@app.get("/api/quote/{symbol}")
def quote(symbol: str, range: str = "3M"):
    check(symbol)
    df, src = history(symbol)
    d = df.tail({"1W": 5, "1M": 22, "3M": 66, "1Y": 260}.get(range, 66)).round(2)
    d.insert(0, "t", d.index.strftime("%d %b"))
    d = d.astype(object).where(d.notna(), None)
    return {"symbol": symbol, "source": src, "price": price(symbol), "candles": d.to_dict("records")}


@app.get("/api/signal/{symbol}")
def signal(symbol: str):
    check(symbol)
    df, _ = history(symbol)
    r, diff = df.iloc[-1], (df.macd - df.signal).tail(4)
    up, dn = ((diff.shift(1) <= 0) & (diff > 0)).any(), ((diff.shift(1) >= 0) & (diff < 0)).any()
    bull = int(sum([r.rsi < 30, r.macd > r.signal, r.close > r.sma50]))
    bear = int(sum([r.rsi > 70, r.macd < r.signal, r.close < r.sma50]))
    if r.rsi < 30 and up:
        t, n, why = "BUY", bull, f"RSI {r.rsi:.1f} is oversold and MACD just crossed above its signal line."
    elif r.rsi > 70 and dn:
        t, n, why = "SELL", bear, f"RSI {r.rsi:.1f} is overbought and MACD just crossed below its signal line."
    else:
        t, n = "HOLD", max(bull, bear)
        why = (f"RSI {r.rsi:.1f}; MACD {'above' if r.macd > r.signal else 'below'} signal; "
               f"price {'above' if r.close > r.sma50 else 'below'} SMA 50. Rules are not aligned.")
    # confidence = share of the 3 rules agreeing, not a prediction probability
    return {"signal": t, "reason": why, "confidence": round(n / 3 * 100),
            "generated_at": datetime.now().isoformat(timespec="seconds")}


@app.get("/api/watchlist")
def watchlist():
    out = []
    for s in SYMBOLS:
        c = history(s)[0]["close"]
        out.append({"symbol": s, "price": round(float(c.iloc[-1]), 2),
                    "change_pct": round(float(c.iloc[-1] / c.iloc[-2] - 1) * 100, 2)})
    return out


class Order(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: int = Field(gt=0)
    order_type: Literal["MARKET", "LIMIT"] = "MARKET"
    limit_price: float | None = None


@app.post("/api/orders")
def place_order(o: Order):
    check(o.symbol)
    p = price(o.symbol)
    if o.order_type == "LIMIT":
        if not o.limit_price:
            raise HTTPException(400, "Limit price required")
        if (o.side == "BUY" and p > o.limit_price) or (o.side == "SELL" and p < o.limit_price):
            raise HTTPException(400, f"Limit not met: market is ₹{p:,.2f}")
    with db() as c:
        return {"message": execute(c, o.symbol, o.side, o.qty, p)}


@app.get("/api/portfolio")
def portfolio():
    with db() as c:
        a = c.execute("SELECT cash, initial FROM account").fetchone()
        hs = c.execute("SELECT * FROM holdings").fetchall()
        real = c.execute("SELECT COALESCE(SUM(pnl),0) FROM trades").fetchone()[0]
    rows, inv, mv, day = [], 0.0, 0.0, 0.0
    for h in hs:
        cl = history(h["symbol"])[0]["close"]
        p, pv = float(cl.iloc[-1]), float(cl.iloc[-2])
        inv += h["qty"] * h["avg"]; mv += h["qty"] * p; day += h["qty"] * (p - pv)
        rows.append({"symbol": h["symbol"], "qty": h["qty"], "avg_price": round(h["avg"], 2), "price": round(p, 2),
                     "unrealized_pnl": round((p - h["avg"]) * h["qty"], 2)})
    value = a["cash"] + mv
    total = value - a["initial"]
    return {"initial": a["initial"], "cash": round(a["cash"], 2), "invested": round(inv, 2), "value": round(value, 2),
            "total_pnl": round(total, 2), "daily_pnl": round(day, 2), "realized_pnl": round(real, 2),
            "unrealized_pnl": round(mv - inv, 2), "return_pct": round(total / a["initial"] * 100, 2), "holdings": rows}


@app.get("/api/trades")
def trades():
    with db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM trades ORDER BY id DESC")]


class Reset(BaseModel):
    capital: float = INITIAL


@app.post("/api/reset")
def reset(r: Reset = Reset()):
    with db() as c:
        c.executescript("DROP TABLE IF EXISTS account; DROP TABLE IF EXISTS holdings; DROP TABLE IF EXISTS trades;")
    init_db(r.capital)
    return {"ok": True}
