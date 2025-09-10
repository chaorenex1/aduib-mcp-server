#!/usr/bin/env bash
WORK_DIR="."

# 颜色输出（可选）
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

log() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*"; }

trap 'err "部署失败"; exit 1' ERR

cd "${WORK_DIR}"

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
echo "已后台运行，PID: $!"
