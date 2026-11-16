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

## Resume bullets (edit to match what you built or changed)
- Built a full-stack paper-trading platform (React, Tailwind, FastAPI, SQLite) with order execution, portfolio tracking, and realized/unrealized P&L.
- Implemented RSI, MACD, moving-average and Bollinger Band calculations in pandas and a rule-based signal engine that reports rule agreement instead of a prediction probability.
- Designed atomic order handling with weighted-average cost basis and validation against cash and holdings; covered it with pytest unit tests.
- Integrated Yahoo Finance market data with a deterministic simulated fallback and clear data-source labelling in the UI.
- Developed a responsive dark-theme trading UI with a custom Recharts candlestick chart, watchlist, and filterable trade history.

## Ideas to extend (good interview talking points)
User auth (JWT), WebSocket price streaming, pending limit orders, Docker Compose, CI running pytest.
