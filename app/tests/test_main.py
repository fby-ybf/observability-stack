"""demo-service 的接口测试（CI 中执行）。"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_items():
    resp = client.get("/api/items")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 10
    assert len(body["items"]) == 10


def test_error_endpoint_returns_500():
    resp = client.get("/api/error")
    assert resp.status_code == 500


def test_metrics_exposed():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    text = resp.text
    assert "demo_requests_total" in text
    assert "demo_request_latency_seconds" in text


def test_latency_recorded():
    client.get("/api/items")
    resp = client.get("/metrics")
    assert 'endpoint="/api/items"' in resp.text
