# dockerfile
FROM python:3.12-slim

# 基本设置
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai
ENV DOCKER_ENV=true
ENV APP_HOST=10.0.0.96
WORKDIR /app

RUN \
  echo "INFO: Attempting to switch main Debian APT sources to mirrors.aliyun.com..." && \
  if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
    echo "INFO: Modifying /etc/apt/sources.list.d/debian.sources" && \
    sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
  elif [ -f /etc/apt/sources.list ]; then \
    echo "INFO: Modifying /etc/apt/sources.list" && \
    sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list && \
    sed -i 's|http://archive.ubuntu.com|http://mirrors.aliyun.com|g' /etc/apt/sources.list; \
  else \
    echo "WARNING: Standard Debian/Ubuntu APT source files not found in expected locations."; \
  fi && \
  echo "INFO: APT sources modification complete."
# 安装系统依赖（用于编译扩展，如 psycopg2）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖描述文件以利用缓存
COPY pyproject.toml uv.lock* .env.production ./

# 安装 uv 包管理器并使用 uv 安装依赖（只安装非 dev 依赖）
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --extra crawler

# 复制项目源码
COPY . .

# 确保日志目录存在
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 5002

# 启动命令：假设 FastAPI app 在 aduib_mcp_server.app:app
CMD ["/app/deploy/aduib_mcp_server.venv.sh"]
