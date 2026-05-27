"""SQLite 连接 + WAL + 表结构初始化。

WAL 模式：写操作不阻塞读，读不阻塞写。多客户端并发场景必开。
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS funds (
    code        TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nav_history (
    fund_code        TEXT NOT NULL,
    date             TEXT NOT NULL,
    nav              REAL NOT NULL,
    accumulated_nav  REAL,
    growth_rate      REAL,
    PRIMARY KEY (fund_code, date)
);
CREATE INDEX IF NOT EXISTS idx_nav_history_date ON nav_history(date);

CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   TEXT UNIQUE,
    fund_code   TEXT NOT NULL,
    date        TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('buy', 'sell')),
    nav         REAL NOT NULL,
    shares      REAL NOT NULL,
    amount      REAL NOT NULL,
    fee         REAL NOT NULL DEFAULT 0,
    note        TEXT,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tx_fund ON transactions(fund_code);
CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);

CREATE TABLE IF NOT EXISTS advice_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code   TEXT NOT NULL,
    signal      TEXT NOT NULL,
    detail      TEXT,
    created_at  TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)
        try:
            conn.execute("ALTER TABLE funds ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # 列已存在
        conn.commit()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
