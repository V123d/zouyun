FROM python:3.10-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装系统依赖（如可能需要编译的基础库）
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单并安装
# 这里使用国内镜像加速
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 将当前目录内容复制到容器里的 /app 目录下
COPY . .

# 暴露 8000 端口
EXPOSE 8000

# 生产级启动：使用 Gunicorn 配合 Uvicorn Worker，增加超时时间以适应长耗时的 AI 生成
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
