# dockerfile
FROM python:3.12-slim

# 基本设置
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai
ENV DOCKER_ENV=true
ENV APP_HOST=10.0.0.96
WORKDIR /app

# 先复制依赖描述文件以利用缓存
COPY pyproject.toml uv.lock* .env.production ./

# 安装 uv 包管理器并使用 uv 安装依赖（只安装非 dev 依赖）
RUN uv sync --frozen --no-dev --extra crawler

# 复制项目源码
COPY . .
RUN chmod +x /app/deploy/aduib_mcp_server.sh

# 确保日志目录存在
RUN mkdir -p /app/logs

# 启动命令：假设 FastAPI app 在 aduib_mcp_server.app:app
CMD ["/app/deploy/aduib_mcp_server.sh"]
