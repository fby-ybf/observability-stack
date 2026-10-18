# observability-stack

一个练手用的「可观测性」最小实践栈：自己写一个带指标的服务，用 Prometheus 采集、
Grafana 看板展示、告警规则验证、脚本巡检，并用 GitHub Actions 跑测试和构建镜像。

技术栈：Python / FastAPI / Docker Compose / Prometheus / Grafana / GitHub Actions

## 架构

```
                 ┌──────────────┐
   浏览器 ──────▶│ demo-service │◀──── Prometheus (抓取 /metrics)
   :8000         │  FastAPI     │        :9090
                 └──────────────┘          │
                       ▲                   ▼
                       │            ┌─────────────┐
                 node-exporter ────▶│   Grafana   │  看板 + 告警
                   :9100            │    :3000    │
                                    └─────────────┘
```

## 快速开始

前置：安装 Docker Desktop（Windows / macOS）或 Docker Engine + compose 插件。

```bash
git clone <你的仓库地址>
cd observability-stack
docker compose up -d
```

启动后：

| 地址 | 内容 |
| --- | --- |
| http://localhost:8000/docs | demo-service 接口文档（Swagger） |
| http://localhost:9090 | Prometheus（Status → Targets 看 3 个目标是否 UP） |
| http://localhost:3000 | Grafana，admin / admin，数据源与看板已自动配置 |
| http://localhost:9100/metrics | 宿主机指标（node-exporter） |

制造一些流量和异常，验证监控是否生效：

```bash
curl http://localhost:8000/api/items      # 正常请求
curl http://localhost:8000/api/slow       # 慢请求 → P95 延迟抬升
curl -i http://localhost:8000/api/error   # 500 → 错误率告警
docker stop demo-service                  # 停服务 → DemoServiceDown 告警
```

Prometheus 的 Alerts 页面（http://localhost:9090/alerts）能看到三条规则的状态变化。

## 目录结构

```
.
├── app/                     # 被监控的服务
│   ├── main.py              #   FastAPI 入口，中间件统一埋点
│   ├── Dockerfile           #   多阶段缓存、非 root 用户、HEALTHCHECK
│   ├── requirements.txt
│   └── tests/test_main.py   #   接口与指标测试（CI 执行）
├── prometheus/
│   ├── prometheus.yml       # 抓取配置（服务 + 节点）
│   └── alert.rules.yml      # 3 条告警：服务失联 / 错误率 / P95 延迟
├── grafana/
│   ├── provisioning/        # 数据源与看板目录的自动挂载配置
│   └── dashboards/          # 看板 JSON：QPS、5xx 比例、P50/P95、错误计数
├── scripts/healthcheck.py   # 巡检脚本：健康检查 + 指标汇总 + 日志扫描
└── .github/workflows/ci.yml # push 时跑 pytest 并构建镜像
```

## 这个项目练到了什么

- **容器化与编排**：多服务 Compose 编排、端口规划、数据卷、容器网络、健康检查、非 root 运行
- **指标与埋点**：Counter / Histogram 的区别与适用场景、PromQL 基础（rate、histogram_quantile、clamp_min）
- **告警设计**：区分 critical / warning，用 `for` 持续时间抑制抖动，避免无意义告警
- **可观测性三支柱里的两件**：metrics + logs（日志扫描脚本），理解 traces 的补齐方向
- **自动化**：Python 巡检脚本 + GitHub Actions 的 test / build 两条流水线

## 后续可扩展

- 加 Loki + Promtail 收集容器日志，把「日志扫描脚本」换成真实日志检索
- 接入 Alertmanager，把告警发到企业微信 / 邮件
- 用 Argo CD / Jenkins 把这个 compose 栈做成一条 CI/CD 流水线
- 给 demo-service 加 OpenTelemetry，打通 traces
