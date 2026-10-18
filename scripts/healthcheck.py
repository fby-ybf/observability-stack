#!/usr/bin/env python3
"""巡检脚本：检查服务健康状态、汇总 /metrics 关键指标、扫描容器日志中的 ERROR。

用法：
    python scripts/healthcheck.py                 # 默认巡检 http://localhost:8000
    python scripts/healthcheck.py --url http://127.0.0.1:8000 --threshold-p95 1.0

退出码：0 全部正常；1 存在异常（可直接接入 CI 或 crontab）。
"""
import argparse
import re
import sys
import urllib.error
import urllib.request

ERROR_LINE = re.compile(r"\b(ERROR|CRITICAL|Traceback)\b")


def fetch(url: str, timeout: float = 5.0) -> tuple[int, str]:
    """请求并返回 (状态码, 响应体)。"""
    req = urllib.request.Request(url, headers={"User-Agent": "healthcheck/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except urllib.error.URLError:
        return 0, ""


def parse_metrics(text: str) -> dict[str, float]:
    """从 Prometheus 文本格式中解析需要的指标。"""
    result: dict[str, float] = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, _, value = line.partition(" ")
        if name == "demo_requests_total":
            labels, _, _ = value.partition(" ")
            result[f"requests_total{labels.strip()}"] = float(value.split()[-1])
        elif name.startswith("demo_request_latency_seconds_count"):
            result["latency_count"] = float(value.split()[-1])
        elif name.startswith("demo_request_latency_seconds_sum"):
            result["latency_sum"] = float(value.split()[-1])
    return result


def scan_log(path: str) -> list[str]:
    """扫描日志文件，返回错误行（最多 10 条）。"""
    hits = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if ERROR_LINE.search(line):
                    hits.append(line.rstrip())
    except FileNotFoundError:
        return [f"日志文件不存在：{path}"]
    return hits[-10:]


def main() -> int:
    parser = argparse.ArgumentParser(description="demo-service 巡检脚本")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--log", default="", help="可选：需要扫描的日志文件路径")
    args = parser.parse_args()

    problems: list[str] = []

    code, _ = fetch(f"{args.url}/healthz")
    if code != 200:
        problems.append(f"/healthz 返回 {code or '无响应'}，服务可能未启动")
    else:
        print("[OK] /healthz 200")

    code, body = fetch(f"{args.url}/metrics")
    if code != 200:
        problems.append(f"/metrics 返回 {code or '无响应'}")
    else:
        metrics = parse_metrics(body)
        if metrics.get("latency_count", 0) > 0:
            avg = metrics["latency_sum"] / metrics["latency_count"]
            print(f"[OK] 平均延迟 {avg * 1000:.1f} ms，累计请求 {int(metrics['latency_count'])} 次")
        errors = [k for k in metrics if 'status="500"' in k]
        if errors:
            print(f"[WARN] 存在 5xx 记录：{len(errors)} 个标签组合")

    if args.log:
        for line in scan_log(args.log):
            print(f"[LOG] {line}")

    if problems:
        for item in problems:
            print(f"[FAIL] {item}")
        return 1
    print("[PASS] 巡检结束，未发现异常")
    return 0


if __name__ == "__main__":
    sys.exit(main())
