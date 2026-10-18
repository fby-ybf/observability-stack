"""demo-service：带 Prometheus 指标的最小 FastAPI 服务。

指标：
  - demo_requests_total{endpoint,method,status}   请求计数
  - demo_request_latency_seconds{endpoint}        请求延迟直方图
  - demo_errors_total{endpoint,type}              业务错误计数
"""
import logging
import random
import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("demo-service")

app = FastAPI(title="demo-service", version="1.0.0")

REQUESTS = Counter("demo_requests_total", "HTTP 请求总数", ["endpoint", "method", "status"])
LATENCY = Histogram(
    "demo_request_latency_seconds",
    "HTTP 请求延迟（秒）",
    ["endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
ERRORS = Counter("demo_errors_total", "业务错误总数", ["endpoint", "type"])


@app.middleware("http")
async def metrics_middleware(request, call_next):
    """统一在中间件里记录 QPS 与延迟，避免每个接口重复埋点。"""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    LATENCY.labels(endpoint=request.url.path).observe(elapsed)
    REQUESTS.labels(
        endpoint=request.url.path, method=request.method, status=response.status_code
    ).inc()
    return response


@app.get("/healthz")
def healthz() -> dict:
    """健康检查：返回 ok 即视为存活。"""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    """就绪检查：可扩展为依赖（数据库/缓存）连通性判断。"""
    return {"status": "ready"}


@app.get("/api/items")
def items() -> dict:
    """正常业务接口，10~200ms 随机延迟。"""
    time.sleep(random.uniform(0.01, 0.2))
    return {"total": 10, "items": [{"id": i, "name": f"item-{i}"} for i in range(10)]}


@app.get("/api/slow")
def slow() -> Response:
    """固定 1.5s 延迟，用于触发 P95 延迟告警。"""
    time.sleep(1.5)
    return JSONResponse({"detail": "slow response"})


@app.get("/api/error")
def error() -> Response:
    """固定返回 500 并打错误日志，用于触发错误率告警。"""
    ERRORS.labels(endpoint="/api/error", type="simulated").inc()
    logger.error("模拟故障：/api/error 被触发")
    return JSONResponse(status_code=500, content={"detail": "internal error"})


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus 抓取入口。"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
