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
            records = [NavRecord(date=f"2026-05-{day:02d}", nav=1.0 + day / 100) for day in range(26, 16, -1)]
            return records, 100

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


def test_get_nav_history_background_fetch(monkeypatch, tmp_path):
    with _patched_db(monkeypatch, tmp_path):
        code = "000003"
        # 预先插入 5 条净值数据
        _insert_nav(
            code,
            [NavRecord(date=f"2026-05-{day:02d}", nav=1.0) for day in range(5, 0, -1)],
        )

        bg_called = []

        async def fake_fetch_nav_history(fetch_code: str, page_size: int, page_index: int = 1):
            bg_called.append((fetch_code, page_size))
            return [NavRecord(date="2026-05-06", nav=1.1)], 10

        monkeypatch.setattr(nav_cache.eastmoney, "fetch_nav_history", fake_fetch_nav_history)

        # 1. 触发后台拉取（数据天数 5 < 10，且 background_fetch=True）
        rows = asyncio.run(nav_cache.get_nav_history(code, days=10, background_fetch=True))
        # 期望：立刻返回本地的 5 条，不阻塞
        assert len(rows) == 5

        # 运行事件循环让后台任务得以启动并执行
        async def run_loop():
            await asyncio.sleep(0.05)

        asyncio.run(run_loop())

        # 检查后台任务是否被成功调用
        assert len(bg_called) == 1
        assert bg_called[0] == (code, 60)


def test_get_nav_history_new_fund_adaptation(monkeypatch, tmp_path):
    with _patched_db(monkeypatch, tmp_path):
        code = "000004"
        called_count = 0
        called_sizes = []

        async def fake_fetch_nav_history(fetch_code: str, page_size: int, page_index: int = 1):
            nonlocal called_count
            called_count += 1
            called_sizes.append(page_size)
            records = [NavRecord(date=f"2026-05-{day:02d}", nav=1.0) for day in range(5, 0, -1)]
            return records, 5

        monkeypatch.setattr(nav_cache.eastmoney, "fetch_nav_history", fake_fetch_nav_history)

        # 1. 首次全量同步：本地为空，同步拉取
        rows = asyncio.run(nav_cache.get_nav_history(code, days=10))
        assert len(rows) == 5
        assert called_count == 1
        assert called_sizes[0] == 60  # max(10, 60)
        assert nav_cache._fund_total_count[code] == 5

        # 2. 第二次拉取：本地已有 5 条，days 请求 10 条
        # 虽然本地天数(5)仍然小于请求天数(10)，但因为已经和东财总数(5)一致，
        # has_enough 应自适应判定为 True，所以仅触发增量同步拉取，page_size 为 10
        nav_cache._nav_refresh_ts[code] = 0.0  # 绕过时间节流
        rows2 = asyncio.run(nav_cache.get_nav_history(code, days=10))
        assert len(rows2) == 5
        assert called_count == 2
        assert called_sizes[1] == 10  # _INCREMENTAL_FETCH_SIZE


def test_fetch_quote_network_retry(monkeypatch):
    from app.services import eastmoney
    import httpx
    import time
    
    called_count = 0
    async def fake_get(*args, **kwargs):
        nonlocal called_count
        called_count += 1
        if called_count == 1:
            raise httpx.ConnectTimeout("Connect Timeout")
        
        class FakeResponse:
            text = 'jsonpgz({"fundcode":"000001","name":"Test Fund","jzrq":"2026-05-28","dwjz":"1.0","gsz":"1.01","gszzl":"1.0","gztime":"2026-05-28 15:00"});'
            def raise_for_status(self):
                pass
        return FakeResponse()

    # mock global get_client 的 client.get
    from app.services.eastmoney import get_client
    client = get_client()
    monkeypatch.setattr(client, "get", fake_get)

    async def fake_sleep(seconds):
        pass
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    quote = asyncio.run(eastmoney.fetch_quote("000001"))
    assert quote is not None
    assert quote.name == "Test Fund"
    assert called_count == 2


def test_get_quote_network_fallback(monkeypatch):
    import httpx
    import time
    async def fake_fetch_quote(code: str):
        raise httpx.RequestError("Request Error")

    monkeypatch.setattr(nav_cache.eastmoney, "fetch_quote", fake_fetch_quote)
    
    nav_cache._quote_cache.clear()
    
    quote = asyncio.run(nav_cache.get_quote("000001"))
    assert quote is None
    
    cached = nav_cache._quote_cache.get("000001")
    assert cached is not None
    assert cached[1] is None
    assert cached[0] > time.time() + 10.0


def test_holdings_router_gather_isolation(monkeypatch, tmp_path):
    from app.routers import holdings
    import time
    with _patched_db(monkeypatch, tmp_path):
        _insert_transaction(code="000005")

        async def fake_get_quote(code: str):
            raise RuntimeError("DB writing error inside quote (not network error)")

        async def fake_get_nav_history(*args, **kwargs):
            raise ValueError("Unexpected validation error inside nav")

        monkeypatch.setattr(nav_cache, "get_quote", fake_get_quote)
        monkeypatch.setattr(nav_cache, "get_nav_history", fake_get_nav_history)

        summary, trade_date = asyncio.run(holdings._get_holdings_summary())
        
        assert len(summary.positions) == 1
        assert summary.positions[0].fund_code == "000005"
        assert summary.positions[0].profit_rate == -1.0

