# dockerfile
FROM aduib-mcp-server-base:latest

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
RUN pip install .

# 复制项目源码
COPY . .

# 确保日志目录存在
RUN mkdir -p /app/logs

ENTRYPOINT ["python","app.py"]
