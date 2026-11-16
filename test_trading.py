import pytest
from fastapi import HTTPException
import main


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", str(tmp_path / "t.db"))
    main.init_db()


def run(side, qty, price):
    with main.db() as c:
        return main.execute(c, "TCS", side, qty, price)


def state():
    with main.db() as c:
        return (c.execute("SELECT cash FROM account").fetchone()[0],
                c.execute("SELECT qty, avg FROM holdings WHERE symbol='TCS'").fetchone())


def test_weighted_average_price():
    run("BUY", 10, 100); run("BUY", 10, 200)
    cash, h = state()
    assert h["qty"] == 20 and h["avg"] == 150 and cash == 100_000 - 3000


def test_sell_realizes_pnl_and_updates_cash():
    run("BUY", 10, 100)
    run("SELL", 4, 130)
    cash, h = state()
    assert h["qty"] == 6 and cash == 100_000 - 1000 + 520
    with main.db() as c:
        assert c.execute("SELECT SUM(pnl) FROM trades").fetchone()[0] == 120


def test_cannot_overspend():
    with pytest.raises(HTTPException):
        run("BUY", 1000, 4000)


def test_cannot_oversell():
    run("BUY", 5, 100)
    with pytest.raises(HTTPException):
        run("SELL", 6, 100)
