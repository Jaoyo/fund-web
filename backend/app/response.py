"""统一响应格式 + 异常处理器。

所有响应：{ "code": 0, "message": "ok", "data": ... }
失败：    { "code": <int>, "message": "...", "data": null }
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class BizError(Exception):
    """业务异常。code 用 4 位数字。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}


async def biz_error_handler(_: Request, exc: BizError) -> JSONResponse:
    return JSONResponse(status_code=200, content=fail(exc.code, exc.message))


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(exc.status_code * 10, str(exc.detail)),
    )


async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=fail(4220, f"参数错误: {exc.errors()}"),
    )


import logging
logger = logging.getLogger("fund.error")


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("服务器未处理的异常错误")
    return JSONResponse(status_code=500, content=fail(5000, f"服务器错误: {exc}"))
