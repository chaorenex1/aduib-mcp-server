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

# 获取当前提交短哈希作为镜像标签
GIT_SHA=$(git rev-parse --short HEAD)
IMAGE_TAG="${IMAGE_NAME}:${GIT_SHA}"
log "当前提交 ${GIT_SHA}，镜像标签 ${IMAGE_TAG}"

# 停止并删除旧容器（如果存在）
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  log "停止并移除旧容器 ${CONTAINER_NAME}"
  docker stop "${CONTAINER_NAME}" || true
  docker rm "${CONTAINER_NAME}" || true
else
  warn "未找到名为 ${CONTAINER_NAME} 的容器"
fi

# 可选：删除同名旧镜像（不删除会保留历史镜像）
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}:"; then
  log "清理同名镜像（保留其它标签）"
  # docker rmi "${IMAGE_NAME}:latest" || true
fi

# 构建新镜像
log "构建镜像 ${IMAGE_TAG}"
docker build -t "${IMAGE_TAG}" -f ./docker/Dockerfile .

# 创建日志目录（宿主机）
mkdir -p "${LOG_HOST_DIR}"

# 运行新容器
log "启动容器 ${CONTAINER_NAME}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  -p "${PORT}:${EXPOSED_PORT}" \
  -v "${LOG_HOST_DIR}:/app/logs" \
  "${IMAGE_TAG}"

# 等待并检查容器状态
sleep 5
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  log "容器 ${CONTAINER_NAME} 启动成功，映射端口 ${PORT}"
  log "访问地址: http://localhost:${PORT}"
  log "最近容器日志："
  docker logs --tail 20 "${CONTAINER_NAME}" || true
else
  err "容器启动失败，查看完整日志："
  docker logs "${CONTAINER_NAME}" || true
  exit 1
fi

log "部署完成：镜像=${IMAGE_TAG} 容器=${CONTAINER_NAME} 工作目录=${WORK_DIR}"