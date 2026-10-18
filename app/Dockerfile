FROM python:3.12-slim

WORKDIR /srv

# 先单独装依赖，利用镜像缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# 用非 root 用户运行，养成基础安全习惯
RUN useradd -r -u 10001 appuser && chown -R appuser /srv
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status==200 else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
