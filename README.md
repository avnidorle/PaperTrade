# PaperTrade

A full-stack paper-trading simulator for educational use. No real money and no broker connection.
React + Tailwind + Recharts frontend, FastAPI + SQLite backend, indicator and signal engine in pandas.

## Run it
Needs Python 3.10+ and Node 18+.

```bash
# terminal 1
cd backend && pip install -r requirements.txt && uvicorn main:app --reload   # http://localhost:8000/docs
# terminal 2
cd frontend && npm install && npm run dev                                    # http://localhost:5173
# tests
cd backend && pytest
```

Prices come from Yahoo Finance (delayed, NSE tickers) when available and fall back to seeded simulated data.
The UI labels which source is in use.

## Architecture
- `backend/main.py`: REST API, SQLite persistence (account, holdings, trades), order execution, indicators (RSI, MACD, SMA/EMA, Bollinger), rule-based BUY/SELL/HOLD signals.
- `backend/test_trading.py`: pytest tests for weighted average price, realized P&L, cash and holdings validation.
- `frontend/src`: `App.jsx` (dashboard, order panel, portfolio, trade log), `Chart.jsx` (custom candlestick + volume), `api.js` (API client).


