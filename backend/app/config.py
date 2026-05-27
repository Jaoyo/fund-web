"""全局配置。读环境变量，提供默认值。"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 先加载 backend/.env（如果存在），不覆盖已设置的环境变量
load_dotenv(BASE_DIR / ".env", override=False)

DB_PATH = DATA_DIR / "fund.db"

API_PREFIX = "/api/v1"

ALLOWED_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

EASTMONEY_QUOTE_URL = "https://fundgz.1234567.com.cn/js/{code}.js"
EASTMONEY_NAV_URL = "https://api.fund.eastmoney.com/f10/lsjz"
EASTMONEY_DETAIL_URL = "https://fund.eastmoney.com/pingzhongdata/{code}.js"
EASTMONEY_REFERER = "https://fund.eastmoney.com/"

QUOTE_TTL_SECONDS = 60
NAV_REFRESH_HOUR = 21
NAV_REFRESH_MINUTE = 0

REQUEST_TIMEOUT = 10.0

DEBUG = os.getenv("FUND_DEBUG", "0") == "1"

AUTH_TOKEN = os.getenv("FUND_AUTH_TOKEN", "").strip()
