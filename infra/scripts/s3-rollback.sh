#!/usr/bin/env bash
# S3 版本回滚脚本
# 用途: 将 S3 Bucket 中的对象批量回滚到指定日期的版本
# 项目: ai-agents-platform

set -euo pipefail

# ============================================================
# 常量定义
# ============================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly PROJECT_NAME="ai-agents-platform"

# ============================================================
# 帮助信息
# ============================================================
usage() {
  cat <<EOF
用法: $SCRIPT_NAME --env <dev|prod> --target-date <YYYY-MM-DD> [选项]

将 S3 Bucket 中指定日期之后的版本变更批量回滚。

必需参数:
  --env <dev|prod>          目标环境
  --target-date <YYYY-MM-DD> 回滚目标日期 (回滚到该日期的状态)

可选参数:
  --bucket-name <name>      S3 Bucket 名称 (默认: ${PROJECT_NAME}-knowledge-<env>)
  --prefix <prefix>         仅回滚指定前缀下的对象
  --dry-run                 仅列出变更，不执行回滚
  --batch-size <n>          每批处理的对象数 (默认: 100)
  -h, --help                显示帮助信息

示例:
  $SCRIPT_NAME --env dev --target-date 2025-01-15
  $SCRIPT_NAME --env prod --target-date 2025-01-15 --dry-run
  $SCRIPT_NAME --env prod --target-date 2025-01-15 --prefix "documents/"
  $SCRIPT_NAME --env dev --target-date 2025-01-15 --bucket-name my-custom-bucket
EOF
  exit 0
}

# ============================================================
# 日志函数
# ============================================================
log_info()  { echo "[INFO]  $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_warn()  { echo "[WARN]  $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }
log_error() { echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }

# ============================================================
# 参数解析
# ============================================================
ENV=""
TARGET_DATE=""
BUCKET_NAME=""
PREFIX=""
DRY_RUN=false
BATCH_SIZE=100

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)          ENV="$2"; shift 2 ;;
    --target-date)  TARGET_DATE="$2"; shift 2 ;;
    --bucket-name)  BUCKET_NAME="$2"; shift 2 ;;
    --prefix)       PREFIX="$2"; shift 2 ;;
    --dry-run)      DRY_RUN=true; shift ;;
    --batch-size)   BATCH_SIZE="$2"; shift 2 ;;
    -h|--help)      usage ;;
    *)              log_error "未知参数: $1"; usage ;;
  esac
done

# 参数验证
if [[ -z "$ENV" ]]; then
  log_error "必须指定 --env 参数 (dev|prod)"
  exit 1
fi

if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
  log_error "--env 仅支持 dev 或 prod"
  exit 1
fi

if [[ -z "$TARGET_DATE" ]]; then
  log_error "必须指定 --target-date 参数 (YYYY-MM-DD)"
  exit 1
fi

# 验证日期格式
if ! date -j -f "%Y-%m-%d" "$TARGET_DATE" "+%Y-%m-%d" &>/dev/null 2>&1; then
  # Linux 兼容
  if ! date -d "$TARGET_DATE" "+%Y-%m-%d" &>/dev/null 2>&1; then
    log_error "日期格式无效: $TARGET_DATE (请使用 YYYY-MM-DD)"
    exit 1
  fi
fi

# 默认 Bucket 名称
if [[ -z "$BUCKET_NAME" ]]; then
  BUCKET_NAME="${PROJECT_NAME}-knowledge-${ENV}"
fi

# ============================================================
# 前置检查
# ============================================================
log_info "检查 AWS CLI 配置..."
if ! aws sts get-caller-identity &>/dev/null; then
  log_error "AWS CLI 未配置或凭证无效"
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
REGION=$(aws configure get region 2>/dev/null || echo "ap-northeast-1")
log_info "AWS 账户: $ACCOUNT_ID | 区域: $REGION | 环境: $ENV"

# 检查 Bucket 是否存在
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
  log_error "Bucket '$BUCKET_NAME' 不存在或无权限访问"
  exit 1
fi

# 检查版本控制是否启用
VERSIONING=$(aws s3api get-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --query 'Status' \
  --output text 2>/dev/null || echo "Disabled")

if [[ "$VERSIONING" != "Enabled" ]]; then
  log_error "Bucket '$BUCKET_NAME' 未启用版本控制 (当前: $VERSIONING)"
  exit 1
fi

log_info "Bucket '$BUCKET_NAME' 版本控制已启用"

# ============================================================
# 步骤 1: 列出指定日期之后的版本变更
# ============================================================
log_info "=========================================="
log_info "步骤 1: 扫描 $TARGET_DATE 之后的版本变更"
log_info "=========================================="

# 转换日期为 ISO 格式用于比较
TARGET_DATETIME="${TARGET_DATE}T23:59:59Z"

# 创建临时文件存储结果
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

VERSIONS_FILE="$TMPDIR/versions.json"
ROLLBACK_PLAN="$TMPDIR/rollback_plan.json"

# 构建版本列表命令
LIST_CMD="aws s3api list-object-versions --bucket $BUCKET_NAME --output json"
if [[ -n "$PREFIX" ]]; then
  LIST_CMD="$LIST_CMD --prefix $PREFIX"
fi

log_info "获取对象版本列表..."
eval "$LIST_CMD" > "$VERSIONS_FILE"

# 使用 Python 分析版本并生成回滚计划
python3 << 'PYTHON_SCRIPT' - "$VERSIONS_FILE" "$ROLLBACK_PLAN" "$TARGET_DATETIME"
import json
import sys
from datetime import datetime

versions_file = sys.argv[1]
rollback_plan_file = sys.argv[2]
target_datetime = sys.argv[3]

with open(versions_file, 'r') as f:
    data = json.load(f)

versions = data.get('Versions', [])
delete_markers = data.get('DeleteMarkers', [])

# 按 Key 分组，找出每个 Key 在目标日期之前的最新版本
key_versions = {}

for v in versions:
    key = v['Key']
    last_modified = v['LastModified']
    version_id = v['VersionId']
    is_latest = v.get('IsLatest', False)

    if key not in key_versions:
        key_versions[key] = {'before': None, 'after': [], 'current_is_after': False}

    if last_modified <= target_datetime:
        # 目标日期之前的版本，保留最新的一个
        if key_versions[key]['before'] is None or last_modified > key_versions[key]['before']['LastModified']:
            key_versions[key]['before'] = {'VersionId': version_id, 'LastModified': last_modified}
    else:
        key_versions[key]['after'].append({'VersionId': version_id, 'LastModified': last_modified})
        if is_latest:
            key_versions[key]['current_is_after'] = True

# 处理 DeleteMarker
for dm in delete_markers:
    key = dm['Key']
    last_modified = dm['LastModified']
    version_id = dm['VersionId']
    is_latest = dm.get('IsLatest', False)

    if key not in key_versions:
        key_versions[key] = {'before': None, 'after': [], 'current_is_after': False}

    if last_modified > target_datetime:
        key_versions[key]['after'].append({
            'VersionId': version_id,
            'LastModified': last_modified,
            'IsDeleteMarker': True,
        })
        if is_latest:
            key_versions[key]['current_is_after'] = True

# 生成回滚计划
plan = {
    'objects_to_rollback': [],
    'versions_to_delete': [],
    'stats': {
        'total_keys_scanned': len(key_versions),
        'keys_affected': 0,
        'versions_to_remove': 0,
    }
}

for key, info in key_versions.items():
    if not info['after'] or not info['current_is_after']:
        continue

    plan['stats']['keys_affected'] += 1

    # 需要删除目标日期之后的所有版本
    for after_v in info['after']:
        plan['versions_to_delete'].append({
            'Key': key,
            'VersionId': after_v['VersionId'],
        })
        plan['stats']['versions_to_remove'] += 1

    target_version = info['before']['VersionId'] if info['before'] else None
    plan['objects_to_rollback'].append({
        'Key': key,
        'TargetVersionId': target_version,
        'AfterVersionCount': len(info['after']),
    })

with open(rollback_plan_file, 'w') as f:
    json.dump(plan, f, indent=2, ensure_ascii=False)

# 输出摘要
print(f"扫描对象数:       {plan['stats']['total_keys_scanned']}")
print(f"受影响对象数:     {plan['stats']['keys_affected']}")
print(f"需删除版本数:     {plan['stats']['versions_to_remove']}")
PYTHON_SCRIPT

# 读取计划统计
KEYS_AFFECTED=$(python3 -c "import json; d=json.load(open('$ROLLBACK_PLAN')); print(d['stats']['keys_affected'])")
VERSIONS_TO_REMOVE=$(python3 -c "import json; d=json.load(open('$ROLLBACK_PLAN')); print(d['stats']['versions_to_remove'])")

if [[ "$KEYS_AFFECTED" -eq 0 ]]; then
  log_info "无需回滚: $TARGET_DATE 之后没有版本变更"
  exit 0
fi

# ============================================================
# 步骤 2: 显示回滚计划
# ============================================================
log_info "=========================================="
log_info "步骤 2: 回滚计划"
log_info "=========================================="

echo ""
echo "================================================"
echo "  S3 版本回滚计划"
echo "================================================"
echo "  Bucket:         $BUCKET_NAME"
echo "  目标日期:       $TARGET_DATE"
echo "  前缀过滤:       ${PREFIX:-无}"
echo "  受影响对象:     $KEYS_AFFECTED"
echo "  待删除版本:     $VERSIONS_TO_REMOVE"
echo "  批处理大小:     $BATCH_SIZE"
echo "================================================"
echo ""

# 显示前 20 个受影响对象
log_info "受影响的对象 (前 20 个):"
python3 -c "
import json
plan = json.load(open('$ROLLBACK_PLAN'))
for obj in plan['objects_to_rollback'][:20]:
    target = obj['TargetVersionId'] or '(将被删除)'
    print(f\"  {obj['Key']} -> {target} (删除 {obj['AfterVersionCount']} 个版本)\")
if len(plan['objects_to_rollback']) > 20:
    print(f'  ... 还有 {len(plan[\"objects_to_rollback\"]) - 20} 个对象')
"

if [[ "$DRY_RUN" == true ]]; then
  log_info "[DRY-RUN] 仅显示回滚计划，不执行实际操作"
  exit 0
fi

# ============================================================
# 步骤 3: 安全确认
# ============================================================
echo ""
if [[ "$ENV" == "prod" ]]; then
  log_warn "即将在 PROD 环境执行 S3 版本回滚！"
  read -r -p "请输入 'ROLLBACK-PROD' 确认: " CONFIRM
  if [[ "$CONFIRM" != "ROLLBACK-PROD" ]]; then
    log_info "已取消操作"
    exit 0
  fi
else
  read -r -p "确认回滚? (y/N): " CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    log_info "已取消操作"
    exit 0
  fi
fi

# ============================================================
# 步骤 4: 执行回滚 (批量删除新版本)
# ============================================================
log_info "=========================================="
log_info "步骤 4: 执行版本回滚"
log_info "=========================================="

DELETED_COUNT=0
FAILED_COUNT=0
BATCH_NUM=0

# 按批次处理
python3 -c "
import json
plan = json.load(open('$ROLLBACK_PLAN'))
versions = plan['versions_to_delete']
batch_size = $BATCH_SIZE

for i in range(0, len(versions), batch_size):
    batch = versions[i:i+batch_size]
    batch_file = '$TMPDIR/batch_' + str(i // batch_size) + '.json'
    delete_request = {
        'Objects': [{'Key': v['Key'], 'VersionId': v['VersionId']} for v in batch],
        'Quiet': True
    }
    with open(batch_file, 'w') as f:
        json.dump(delete_request, f)
    print(batch_file)
" | while read -r BATCH_FILE; do
  BATCH_NUM=$((BATCH_NUM + 1))
  BATCH_COUNT=$(python3 -c "import json; print(len(json.load(open('$BATCH_FILE'))['Objects']))")

  log_info "处理批次 $BATCH_NUM ($BATCH_COUNT 个版本)..."

  RESULT=$(aws s3api delete-objects \
    --bucket "$BUCKET_NAME" \
    --delete "file://$BATCH_FILE" \
    --output json 2>&1) || true

  ERRORS=$(echo "$RESULT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    errors = data.get('Errors', [])
    print(len(errors))
except:
    print(0)
" 2>/dev/null || echo "0")

  if [[ "$ERRORS" -gt 0 ]]; then
    log_warn "批次 $BATCH_NUM: $ERRORS 个版本删除失败"
    FAILED_COUNT=$((FAILED_COUNT + ERRORS))
  fi

  DELETED_COUNT=$((DELETED_COUNT + BATCH_COUNT - ERRORS))
done

# ============================================================
# 步骤 5: 验证回滚完整性
# ============================================================
log_info "=========================================="
log_info "步骤 5: 验证回滚完整性"
log_info "=========================================="

# 重新扫描检查是否还有目标日期之后的版本作为最新版
VERIFY_CMD="aws s3api list-object-versions --bucket $BUCKET_NAME --output json"
if [[ -n "$PREFIX" ]]; then
  VERIFY_CMD="$VERIFY_CMD --prefix $PREFIX"
fi

eval "$VERIFY_CMD" > "$TMPDIR/verify.json"

REMAINING=$(python3 -c "
import json
data = json.load(open('$TMPDIR/verify.json'))
target = '$TARGET_DATETIME'
count = 0
for v in data.get('Versions', []):
    if v.get('IsLatest', False) and v['LastModified'] > target:
        count += 1
print(count)
")

echo ""
echo "================================================"
echo "  回滚结果"
echo "================================================"
echo "  Bucket:           $BUCKET_NAME"
echo "  目标日期:         $TARGET_DATE"
echo "  受影响对象:       $KEYS_AFFECTED"
echo "  已删除版本:       约 $VERSIONS_TO_REMOVE"
echo "  回滚后仍有新版:  $REMAINING"
echo "================================================"
echo ""

if [[ "$REMAINING" -eq 0 ]]; then
  log_info "回滚验证通过: 所有对象已恢复到 $TARGET_DATE 的状态"
else
  log_warn "回滚验证: 仍有 $REMAINING 个对象的最新版本晚于目标日期"
  log_warn "可能原因: 并发写入或删除权限不足，请手动检查"
fi

log_info "回滚操作完成"
