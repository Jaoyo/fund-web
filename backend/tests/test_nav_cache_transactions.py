from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import asyncio

from app import db
from app.models.fund import NavRecord
from app.routers import transactions
from app.services import nav_cache


@contextmanager
def _patched_db(monkeypatch, tmp_path):
    db_path = tmp_path / "fund.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    monkeypatch.setattr(nav_cache, "get_conn", db.get_conn)
    monkeypatch.setattr(transactions, "get_conn", db.get_conn)
    db.init_db()
    yield


def _insert_nav(code: str, records: list[NavRecord]) -> None:
    with db.get_conn() as conn:
        conn.executemany(
            "INSERT INTO nav_history(fund_code, date, nav, accumulated_nav, growth_rate) "
            "VALUES (?, ?, ?, ?, ?)",
            [(code, r.date, r.nav, r.accumulated_nav, r.growth_rate) for r in records],
        )


def _insert_transaction(
    *,
    client_id: str | None = None,
    code: str = "000001",
    date: str = "2026-01-02",
    type_: str = "buy",
    nav: float = 1.0,
    shares: float = 100.0,
    amount: float = 100.0,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with db.get_conn() as conn:
        conn.execute(
            "INSERT INTO funds(code, name, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(code) DO UPDATE SET name=excluded.name, updated_at=excluded.updated_at",
            (code, "Test Fund", now),
        )
        conn.execute(
            "INSERT INTO transactions"
            "(client_id, fund_code, date, type, nav, shares, amount, fee, note, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (client_id, code, date, type_, nav, shares, amount, 0, None, now),
        )


def test_throttled_nav_history_still_fetches_when_cache_has_too_few_days(monkeypatch, tmp_path):
    with _patched_db(monkeypatch, tmp_path):
        code = "000001"
        _insert_nav(
            code,
            [
                NavRecord(date="2026-05-26", nav=1.1),
                NavRecord(date="2026-05-25", nav=1.0),
            ],
        )
        nav_cache._nav_refresh_ts[code] = 9999999999.0

        async def fake_fetch_nav_history(fetch_code: str, page_size: int, page_index: int = 1):
            assert fetch_code == code
            assert page_size >= 30
            return [NavRecord(date=f"2026-05-{day:02d}", nav=1.0 + day / 100) for day in range(26, 16, -1)]

        monkeypatch.setattr(nav_cache.eastmoney, "fetch_nav_history", fake_fetch_nav_history)

        rows = asyncio.run(nav_cache.get_nav_history(code, days=10))

    assert len(rows) == 10


def test_sync_pending_fetches_history_back_to_earliest_pending_date(monkeypatch, tmp_path):
    with _patched_db(monkeypatch, tmp_path):
        _insert_transaction(
            code="000002",
            date="2026-03-01",
            type_="buy",
            nav=0.0,
            shares=0.0,
            amount=1000.0,
        )

        requested_days = []

        async def fake_get_nav_history(code: str, days: int = 60):
            requested_days.append(days)
            return [NavRecord(date="2026-03-01", nav=2.0)]

        monkeypatch.setattr(nav_cache, "get_nav_history", fake_get_nav_history)

        synced = asyncio.run(nav_cache.sync_pending_transactions())

        with db.get_conn() as conn:
            row = conn.execute("SELECT nav, shares, amount FROM transactions").fetchone()

    assert synced == 1
    assert requested_days[0] > 30
    assert row["nav"] == 2.0
    assert row["shares"] == 500.0
    assert row["amount"] == 1000.0


def test_create_transaction_idempotent_hit_returns_before_external_calls(monkeypatch, tmp_path):
    with _patched_db(monkeypatch, tmp_path):
        _insert_transaction(client_id="same-client-id")

        async def fail_get_nav_history(*args, **kwargs):
            raise AssertionError("nav history should not be called for idempotent hit")

        async def fail_get_quote(*args, **kwargs):
            raise AssertionError("quote should not be called for idempotent hit")

        async def fail_fetch_fund_info(*args, **kwargs):
            raise AssertionError("fund info should not be called for idempotent hit")

        monkeypatch.setattr(transactions.nav_cache, "get_nav_history", fail_get_nav_history)
        monkeypatch.setattr(transactions.nav_cache, "get_quote", fail_get_quote)
        monkeypatch.setattr(transactions.eastmoney, "fetch_fund_info", fail_fetch_fund_info)

        payload = transactions.TransactionIn(
            client_id="same-client-id",
            fund_code="000001",
            date="2026-01-02",
            type="buy",
            amount=100.0,
        )

        resp = asyncio.run(transactions.create_transaction(payload))

    assert resp["code"] == 0
    assert resp["message"] == "idempotent hit"
    assert resp["data"]["client_id"] == "same-client-id"
