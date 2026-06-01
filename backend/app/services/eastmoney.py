"""天天基金（东方财富）接口封装。

所有接口都是公开 GET，但必须带 Referer 头，否则会被拒。
"""
from __future__ import annotations

import json
import re
from typing import Optional

import asyncio
import httpx

from ..config import (
    EASTMONEY_DETAIL_URL,
    EASTMONEY_NAV_URL,
    EASTMONEY_QUOTE_URL,
    EASTMONEY_REFERER,
    REQUEST_TIMEOUT,
)
from ..models.fund import Fund, NavRecord, Quote
from ..response import BizError

import logging
import time

logger = logging.getLogger("fund.eastmoney")

_client: httpx.AsyncClient | None = None
_SEMAPHORE = asyncio.Semaphore(5)
_QUOTE_TIMEOUT = httpx.Timeout(connect=3.0, read=3.0, write=3.0, pool=1.0)
_NAV_TIMEOUT = httpx.Timeout(connect=3.0, read=5.0, write=3.0, pool=1.0)


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=_HEADERS)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


_HEADERS = {
    "Referer": EASTMONEY_REFERER,
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
    ),
}

_JSONP_RE = re.compile(r"jsonpgz\((.*)\)")


async def fetch_quote(code: str) -> Optional[Quote]:
    """盘中实时估值。盘后/节假日返回 None。

    接口返回形如：jsonpgz({"fundcode":"...","name":"...",...});
    """
    url = EASTMONEY_QUOTE_URL.format(code=code)
    client = get_client()
    resp = None
    max_retries = 2
    for attempt in range(max_retries):
        t0 = time.time()
        try:
            async with _SEMAPHORE:
                resp = await client.get(url, timeout=_QUOTE_TIMEOUT)
            resp.raise_for_status()
            elapsed = time.time() - t0
            logger.info("fetch_quote: request success for fund %s, attempt: %d, elapsed: %.3fs", code, attempt + 1, elapsed)
            break
        except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
            elapsed = time.time() - t0
            logger.error("fetch_quote: network error for fund %s, attempt: %d, elapsed: %.3fs, error: %s", code, attempt + 1, elapsed, e)
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(0.5)

    text = resp.text.strip()

    if not text or text == "jsonpgz();":
        return None

    m = _JSONP_RE.search(text)
    if not m:
        raise BizError(5002, f"estimate quote 格式异常: {text[:80]}")

    payload = json.loads(m.group(1))
    return Quote(
        code=payload.get("fundcode", code),
        name=payload.get("name", ""),
        nav_date=payload.get("jzrq", ""),
        nav=float(payload.get("dwjz", 0) or 0),
        estimated_nav=_to_float(payload.get("gsz")),
        estimated_growth=_to_float(payload.get("gszzl")),
        estimated_time=payload.get("gztime"),
    )


_PER_PAGE = 20  # 东财 lsjz 接口每页实际上限是 20，超过会被静默截断


async def fetch_nav_history(
    code: str, page_size: int = 60, page_index: int = 1
) -> tuple[list[NavRecord], int]:
    """历史净值。page_size 是想要的总条数，内部按 _PER_PAGE 分页拉，支持并发加速。"""
    t0 = time.time()
    out: list[NavRecord] = []
    
    async def _fetch_page(client: httpx.AsyncClient, p_idx: int) -> tuple[list[NavRecord], int]:
        params = {"fundCode": code, "pageIndex": p_idx, "pageSize": _PER_PAGE}
        resp = None
        max_retries = 2
        for attempt in range(max_retries):
            t_page_0 = time.time()
            try:
                async with _SEMAPHORE:
                    resp = await client.get(EASTMONEY_NAV_URL, params=params, timeout=_NAV_TIMEOUT)
                resp.raise_for_status()
                break
            except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as ex:
                logger.error("fetch_nav_history: page %d network error for fund %s, elapsed: %.3fs, error: %s", p_idx, code, time.time() - t_page_0, ex)
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.5)
        payload = resp.json()
        items = (payload.get("Data") or {}).get("LSJZList") or []
        records = []
        for it in items:
            records.append(
                NavRecord(
                    date=it["FSRQ"],
                    nav=float(it["DWJZ"] or 0),
                    accumulated_nav=_to_float(it.get("LJJZ")),
                    growth_rate=_to_float(_strip_percent(it.get("JZZZL"))),
                )
            )
        total = payload.get("TotalCount") or 0
        return records, total

    client = get_client()
    # 先拉第一页，获取总数
    first_page_records, total_count = await _fetch_page(client, page_index)
    out.extend(first_page_records)
    
    if not first_page_records or len(out) >= page_size or len(out) >= total_count:
        res = out[:page_size]
        logger.info("fetch_nav_history: fetch completed for fund %s, fetched %d records, total elapsed: %.3fs", code, len(res), time.time() - t0)
        return res, total_count
        
    # 计算还需要拉取的页码
    remaining_needed = min(page_size, total_count) - len(out)
    pages_needed = (remaining_needed + _PER_PAGE - 1) // _PER_PAGE
    
    # 并发拉取剩余所有页
    tasks = [
        _fetch_page(client, page_index + i + 1)
        for i in range(pages_needed)
    ]
    
    # 并发执行并按顺序收集结果
    results = await asyncio.gather(*tasks)
    for records, _ in results:
        out.extend(records)
        
    res = out[:page_size]
    logger.info("fetch_nav_history: fetch completed for fund %s, fetched %d records, total elapsed: %.3fs", code, len(res), time.time() - t0)
    return res, total_count


async def fetch_fund_info(code: str, quote: Optional[Quote] = None) -> Fund:
    """基本信息。优先用 quote 的 name，否则解析 pingzhongdata。"""
    if quote is None:
        quote = await fetch_quote(code)
    if quote and quote.name:
        return Fund(code=code, name=quote.name)

    url = EASTMONEY_DETAIL_URL.format(code=code)
    t0 = time.time()
    try:
        client = get_client()
        async with _SEMAPHORE:
            resp = await client.get(url)
        resp.raise_for_status()
        text = resp.text
        logger.info("fetch_fund_info: details fetched success for fund %s, elapsed: %.3fs", code, time.time() - t0)
    except Exception as e:
        logger.error("fetch_fund_info: details fetch failed for fund %s, elapsed: %.3fs, error: %s", code, time.time() - t0, e)
        raise

    name_match = re.search(r'fS_name\s*=\s*"([^"]+)"', text)
    type_match = re.search(r'fund_sourceRate\s*=\s*"[^"]*";\s*var\s+fund_Rate', text)
    if not name_match:
        raise BizError(4040, f"基金代码 {code} 不存在或无法解析")

    return Fund(code=code, name=name_match.group(1))


def _to_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _strip_percent(v) -> Optional[str]:
    if v is None or v == "":
        return None
    s = str(v).strip().rstrip("%")
    return s or None

async def fetch_fund_stock_holdings(code: str, depth: int = 0, default_proportion: float = 100.0) -> list[dict]:
    """
    抓取基金的重仓股（按比例折算）。
    如果遇到 FOF / ETF 联接基金，会递归抓取其底层的基金持仓，最多向下穿透 2 层。
    """
    if depth > 2:
        return []

    from ..db import get_conn
    from datetime import datetime, timedelta, timezone

    # 1. 尝试读缓存 (30天过期)
    cache_key = f"holdings_{code}"
    with get_conn() as conn:
        row = conn.execute("SELECT value, updated_at FROM api_cache WHERE key = ?", (cache_key,)).fetchone()
        if row:
            updated_at_dt = datetime.fromisoformat(row["updated_at"])
            if datetime.now(timezone.utc) - updated_at_dt < timedelta(days=30):
                return json.loads(row["value"])

    # 2. 缓存未命中或已过期，发请求拉取
    url = f"https://fundmobapi.eastmoney.com/FundMNewApi/FundMNInverstPosition?FCODE={code}&deviceid=Wap&plat=Wap&product=EFund&version=2.0.0"
    try:
        client = get_client()
        async with _SEMAPHORE:
            resp = await client.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("Success"):
            logger.warning("fetch_fund_stock_holdings: failed to fetch for %s", code)
            return []
            
        datas = data.get("Datas", {})
    except Exception as e:
        logger.error("fetch_fund_stock_holdings: network error for %s: %s", code, e)
        return []

    stocks_result = []

    # 3. 处理普通股票持仓
    for s in datas.get("fundStocks") or []:
        proportion = _to_float(s.get("JZBL"))
        if proportion is None:
            continue
        stocks_result.append({
            "stock_code": s.get("GPDM"),
            "stock_name": s.get("GPJC"),
            "proportion": (proportion * default_proportion) / 100.0
        })

    # 4. 处理 FOF 持有其他基金的递归穿透
    for f in datas.get("fundfofs") or []:
        f_code = f.get("TZJJDM")
        f_prop = _to_float(f.get("ZJZBL"))
        if f_code and f_prop:
            actual_prop = (f_prop * default_proportion) / 100.0
            sub_stocks = await fetch_fund_stock_holdings(f_code, depth + 1, actual_prop)
            stocks_result.extend(sub_stocks)
            
    # 5. 处理 ETF 联接基金（只有 ETFCODE，没有确切占比的情况，按100%穿透）
    etf_code = datas.get("ETFCODE")
    if etf_code and not (datas.get("fundStocks") or datas.get("fundfofs")):
        sub_stocks = await fetch_fund_stock_holdings(etf_code, depth + 1, default_proportion)
        stocks_result.extend(sub_stocks)

    # 聚合重复的股票（可能在多个 FOF 里重复持仓）
    agg_map = {}
    for s in stocks_result:
        k = s["stock_code"]
        if k not in agg_map:
            agg_map[k] = s
        else:
            agg_map[k]["proportion"] += s["proportion"]
            
    final_stocks = list(agg_map.values())

    # 6. 写入缓存
    if final_stocks:
        now_str = datetime.now(timezone.utc).isoformat()
        with get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO api_cache (key, value, updated_at) VALUES (?, ?, ?)",
                (cache_key, json.dumps(final_stocks), now_str)
            )

    return final_stocks
