"""FastAPI 入口。"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGIN_REGEX, API_PREFIX
from .db import init_db
from .deps.auth import require_token
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
    import logging
    from logging.handlers import RotatingFileHandler
    from .config import BASE_DIR
    
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    root_logger.addHandler(file_handler)

    # Redirect uvicorn loggers to the file handler and remove console printing
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        ul = logging.getLogger(logger_name)
        for h in list(ul.handlers):
            ul.removeHandler(h)
        ul.addHandler(file_handler)
        ul.propagate = False

    init_db()
    start_scheduler()
    yield
    stop_scheduler()
    from .services import eastmoney
    await eastmoney.close_client()


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

app.include_router(funds.router, prefix=API_PREFIX, dependencies=[Depends(require_token)])
app.include_router(holdings.router, prefix=API_PREFIX, dependencies=[Depends(require_token)])
app.include_router(transactions.router, prefix=API_PREFIX, dependencies=[Depends(require_token)])
app.include_router(quotes.router, prefix=API_PREFIX, dependencies=[Depends(require_token)])
app.include_router(advice.router, prefix=API_PREFIX, dependencies=[Depends(require_token)])


@app.get("/")
async def root() -> dict:
    return ok({"name": "fund-web", "docs": "/docs"})


@app.get(f"{API_PREFIX}/health")
async def health() -> dict:
    return ok({"status": "up"})
