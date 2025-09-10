#!/usr/bin/env bash
# 配置项（根据需要修改）
PROJECT_NAME="aduib-mcp-server"
REPO_URL="https://github.com/chaorenex1/aduib-mcp-server.git"
BRANCH="main"
WORK_DIR="./${PROJECT_NAME}"
CONTAINER_NAME="${PROJECT_NAME}-app"
IMAGE_NAME="${PROJECT_NAME}"
PORT=5002
LOG_HOST_DIR="${WORK_DIR}/logs"
EXPOSED_PORT=5002

# 颜色输出（可选）
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

log() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*"; }

trap 'err "部署失败"; exit 1' ERR

log "开始部署 ${PROJECT_NAME} 到 ${WORK_DIR}"

# 创建工作目录并切换
sudo mkdir -p "${WORK_DIR}"
sudo chown -R "$(id -u):$(id -g)" "${WORK_DIR}" || true
cd "${WORK_DIR}"

# 克隆或更新代码
if [ -d ".git" ]; then
  log "仓库已存在，拉取远端 ${BRANCH}"
  git fetch origin "${BRANCH}"
  git checkout "${BRANCH}"
  git reset --hard "origin/${BRANCH}"
  git clean -fd
else
  log "克隆仓库 ${REPO_URL}"
  rm -rf ./*
  git clone --branch "${BRANCH}" "${REPO_URL}" .
fi

# 如果没有虚拟环境就创建一个
if [ ! -d ".venv" ]; then
    echo "⚡ 创建虚拟环境..."
    uv venv .venv
fi
cp -r ".env.production" ".env"
uv sync --frozen --no-dev --extra crawler
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    source .venv/bin/activate
    playwright install
fi
export PYTHONUNBUFFERED=1
export PYTHONPATH="${WORK_DIR}"
nohup .venv/bin/python app.py > /dev/null 2>&1 &
# 输出进程号
echo "${PROJECT_NAME}脚本已后台运行，PID: $!"
