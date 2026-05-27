"""鉴权依赖。单 token Bearer 校验。"""
from __future__ import annotations

import hmac

from fastapi import Header

from .. import config
from ..response import BizError


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not config.AUTH_TOKEN:
        raise BizError(5001, "服务器未配置 AUTH_TOKEN")

    if not authorization or not authorization.startswith("Bearer "):
        raise BizError(4011, "未登录或 token 无效")

    presented = authorization[len("Bearer "):].strip()
    if not hmac.compare_digest(presented, config.AUTH_TOKEN):
        raise BizError(4011, "未登录或 token 无效")
