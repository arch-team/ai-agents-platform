#!/bin/bash
# =============================================================================
# AI Agents Platform 性能压测运行脚本
#
# 用法:
#   ./run.sh                          # 默认: 50 并发, 5 分钟, localhost:8000
#   ./run.sh --users 100 --time 10m   # 自定义: 100 并发, 10 分钟
#   API_HOST=https://api.example.com ./run.sh  # 指定远程目标
#
# 环境变量:
#   API_HOST                 - API 基础地址 (默认: http://localhost:8000)
#   LOADTEST_USER_EMAIL      - 测试用户邮箱 (默认: loadtest@example.com)
#   LOADTEST_USER_PASSWORD   - 测试用户密码 (默认: LoadTest1234)
#   LOADTEST_P95_THRESHOLD_MS - P95 延迟阈值 (默认: 300ms)
# =============================================================================

set -euo pipefail

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 默认参数
HOST="${API_HOST:-http://localhost:8000}"
USERS="${1:-50}"
SPAWN_RATE="${2:-10}"
RUN_TIME="${3:-5m}"
RESULTS_DIR="results"

# 解析命名参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --users)
            USERS="$2"
            shift 2
            ;;
        --rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        --time)
            RUN_TIME="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# 创建结果目录
mkdir -p "${RESULTS_DIR}"

# 生成带时间戳的报告文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_PREFIX="${RESULTS_DIR}/report_${TIMESTAMP}"

echo "============================================================"
echo " AI Agents Platform 性能压测"
echo "============================================================"
echo " 目标地址:    ${HOST}"
echo " 并发用户:    ${USERS}"
echo " 加压速率:    ${SPAWN_RATE} 用户/秒"
echo " 运行时长:    ${RUN_TIME}"
echo " P95 阈值:    ${LOADTEST_P95_THRESHOLD_MS:-300}ms"
echo " 报告文件:    ${REPORT_PREFIX}_stats.csv"
echo "============================================================"
echo ""

# 检查 locust 是否已安装
if ! command -v locust &> /dev/null; then
    echo "[错误] locust 未安装，请执行: pip install -r requirements.txt"
    exit 1
fi

# 检查目标服务是否可达
echo "[检查] 验证目标服务可达性..."
if curl -sf "${HOST}/health" > /dev/null 2>&1; then
    echo "[通过] 目标服务 ${HOST} 可达"
elif curl -sf "${HOST}/api/v1/auth/me" > /dev/null 2>&1; then
    echo "[通过] 目标服务 ${HOST} 可达 (无 /health 端点)"
else
    echo "[警告] 无法连接到 ${HOST}，压测可能会大量报错"
    echo "  请确认服务已启动: uv run uvicorn src.presentation.api.main:app --port 8000"
    read -p "  是否继续? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "[启动] 开始压测..."
echo ""

# 运行 locust
locust -f locustfile.py \
    --headless \
    -u "${USERS}" \
    -r "${SPAWN_RATE}" \
    --run-time "${RUN_TIME}" \
    --host "${HOST}" \
    --csv "${REPORT_PREFIX}" \
    --csv-full-history \
    --print-stats \
    --only-summary

echo ""
echo "[完成] 压测结束"
echo ""
echo "报告文件:"
echo "  统计摘要:  ${REPORT_PREFIX}_stats.csv"
echo "  历史数据:  ${REPORT_PREFIX}_stats_history.csv"
echo "  失败请求:  ${REPORT_PREFIX}_failures.csv"
echo "  异常信息:  ${REPORT_PREFIX}_exceptions.csv"
