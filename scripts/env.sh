#!/usr/bin/env bash
set -e

# ===== 基本运行环境 =====
export PYTHONUNBUFFERED=1
export PYTHONPATH=$(pwd)
export TZ=Asia/Shanghai
export DOCKER_ENV=false
export APP_HOST=0.0.0.0

# ===== uv 虚拟环境路径 =====
export UV_VENV=".venv"