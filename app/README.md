# demo-service

一个用于「监控与可观测性」练习的最小 FastAPI 服务：自带指标暴露、健康检查、
模拟延迟与错误接口，配合仓库根目录的 `docker-compose.yml` 由 Prometheus 采集、
Grafana 展示。

## 本地运行

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 接口

| 路径 | 说明 |
| --- | --- |
| `GET /healthz` | 健康检查（供 Docker healthcheck / 脚本巡检用） |
| `GET /api/items` | 正常业务接口，带 10~200ms 模拟延迟 |
| `GET /api/slow` | 固定 1.5s 延迟，用于验证慢请求告警 |
| `GET /api/error` | 固定返回 500，用于验证错误率告警 |
| `GET /metrics` | Prometheus 指标（请求量 / 延迟直方图 / 错误计数） |

## 测试

```bash
pip install -r requirements.txt pytest httpx
pytest -q
```
