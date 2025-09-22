# Dockerfile
FROM python:3.13-slim

# 基础优化：更快日志、更少 pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 工作目录
WORKDIR /app

# 先拷 requirements 再装依赖（提高缓存命中率）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝源码
COPY . .

# 容器对外暴露的端口（文档性，实际映射在 docker run）
EXPOSE 8000

# 启动命令（FastAPI）
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
