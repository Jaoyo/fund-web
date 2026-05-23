"""FastAPI 入口。"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGIN_REGEX, API_PREFIX
from .db import init_db
from .response import (
    BizError,
    biz_error_handler,
    http_exception_handler,
    ok,
    unhandled_error_handler,
    validation_error_handler,
)
from .routers import advice, funds, holdings, quotes, transactions
from .tasks.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="fund-web API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(BizError, biz_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(funds.router, prefix=API_PREFIX)
app.include_router(holdings.router, prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(quotes.router, prefix=API_PREFIX)
app.include_router(advice.router, prefix=API_PREFIX)


@app.get("/")
async def root() -> dict:
    return ok({"name": "fund-web", "docs": "/docs"})


@app.get(f"{API_PREFIX}/health")
async def health() -> dict:
    return ok({"status": "up"})
