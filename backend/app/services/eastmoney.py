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
