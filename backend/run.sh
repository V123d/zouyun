#!/bin/bash
# 生产环境 Gunicorn + Uvicorn 挂载脚本
# 支持通过环境变量 PORT 指定端口，默认 8000
# 支持通过 WORKERS 指定工作进程数，默认 4

PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}

echo "Starting Server on port $PORT with $WORKERS workers..."
exec gunicorn app.main:app -w $WORKERS -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
