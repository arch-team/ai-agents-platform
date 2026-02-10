#!/usr/bin/env bash
# 一键启动本地开发环境
# 用法: ./scripts/docker-dev.sh [up|down|logs|restart|reset]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

usage() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  up       启动所有服务 (默认)"
    echo "  down     停止并移除容器"
    echo "  logs     查看后端服务日志"
    echo "  restart  重启后端服务 (重新构建)"
    echo "  reset    完全重置 (删除数据卷)"
    echo "  status   查看服务状态"
}

cmd="${1:-up}"

case "$cmd" in
    up)
        echo "==> 启动开发环境..."
        docker compose -f "$COMPOSE_FILE" up --build -d
        echo ""
        echo "==> 等待服务就绪..."
        sleep 5
        echo "==> 服务状态:"
        docker compose -f "$COMPOSE_FILE" ps
        echo ""
        echo "后端 API: http://localhost:8000"
        echo "API 文档: http://localhost:8000/docs"
        echo "Health:   http://localhost:8000/health"
        ;;
    down)
        echo "==> 停止服务..."
        docker compose -f "$COMPOSE_FILE" down
        ;;
    logs)
        docker compose -f "$COMPOSE_FILE" logs -f backend
        ;;
    restart)
        echo "==> 重启后端服务..."
        docker compose -f "$COMPOSE_FILE" up --build -d backend
        ;;
    reset)
        echo "==> 完全重置 (删除数据卷)..."
        docker compose -f "$COMPOSE_FILE" down -v
        echo "==> 重新启动..."
        docker compose -f "$COMPOSE_FILE" up --build -d
        ;;
    status)
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    *)
        usage
        exit 1
        ;;
esac
