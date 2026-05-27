"""鉴权依赖的端到端测试。

依赖 conftest.py 设置的 FUND_AUTH_TOKEN=test-token。
覆盖：无 header、错 token、对 token、未配置 token。
"""
from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def _build_client():
    # 重新载入 config 让 AUTH_TOKEN 跟当前环境变量同步
    from app import config as config_module  # noqa: PLC0415
    from app import main as main_module  # noqa: PLC0415

    importlib.reload(config_module)
    importlib.reload(main_module)
    return TestClient(main_module.app)


def test_protected_route_without_header():
    with _build_client() as client:
        resp = client.get("/api/v1/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 4011


def test_protected_route_with_wrong_token():
    with _build_client() as client:
        resp = client.get(
            "/api/v1/transactions",
            headers={"Authorization": "Bearer wrong-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 4011


def test_protected_route_with_correct_token():
    with _build_client() as client:
        resp = client.get(
            "/api/v1/transactions",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)


def test_health_remains_public():
    with _build_client() as client:
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


def test_missing_server_token(monkeypatch):
    monkeypatch.setenv("FUND_AUTH_TOKEN", "")
    with _build_client() as client:
        resp = client.get("/api/v1/transactions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 5001
