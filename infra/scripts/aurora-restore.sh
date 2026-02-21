#!/usr/bin/env bash
# Aurora 集群快照恢复脚本
# 用途: 从最新自动备份恢复 Aurora MySQL 集群
# 项目: ai-agents-platform

set -euo pipefail

# ============================================================
# 常量定义
# ============================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly PROJECT_NAME="ai-agents-platform"
readonly DB_ENGINE="aurora-mysql"
readonly RESTORE_SUFFIX="restored-$(date +%Y%m%d-%H%M%S)"

# ============================================================
# 帮助信息
# ============================================================
usage() {
  cat <<EOF
用法: $SCRIPT_NAME --env <dev|prod> [选项]

从最新自动备份恢复 Aurora MySQL 集群。

必需参数:
  --env <dev|prod>          目标环境

可选参数:
  --snapshot-id <id>        指定快照 ID (默认使用最新自动备份)
  --new-cluster-id <id>     恢复后的集群 ID (默认: 原集群ID-${RESTORE_SUFFIX})
  --skip-dns                跳过 DNS/CNAME 切换步骤
  --dry-run                 仅显示恢复计划，不执行
  -h, --help                显示帮助信息

示例:
  $SCRIPT_NAME --env dev
  $SCRIPT_NAME --env prod --snapshot-id rds:ai-agents-plat-db-prod-2025-01-15-00-05
  $SCRIPT_NAME --env prod --dry-run
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
SNAPSHOT_ID=""
NEW_CLUSTER_ID=""
SKIP_DNS=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)        ENV="$2"; shift 2 ;;
    --snapshot-id) SNAPSHOT_ID="$2"; shift 2 ;;
    --new-cluster-id) NEW_CLUSTER_ID="$2"; shift 2 ;;
    --skip-dns)   SKIP_DNS=true; shift ;;
    --dry-run)    DRY_RUN=true; shift ;;
    -h|--help)    usage ;;
    *)            log_error "未知参数: $1"; usage ;;
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

# ============================================================
# 环境配置
# ============================================================
# 集群标识符根据 CDK Stack 命名规则推导
SOURCE_CLUSTER_ID="${PROJECT_NAME}-db-${ENV}"

if [[ -z "$NEW_CLUSTER_ID" ]]; then
  NEW_CLUSTER_ID="${SOURCE_CLUSTER_ID}-${RESTORE_SUFFIX}"
fi

# ============================================================
# 前置检查
# ============================================================
log_info "检查 AWS CLI 配置..."
if ! aws sts get-caller-identity &>/dev/null; then
  log_error "AWS CLI 未配置或凭证无效，请先执行 aws configure"
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
REGION=$(aws configure get region 2>/dev/null || echo "ap-northeast-1")
log_info "AWS 账户: $ACCOUNT_ID | 区域: $REGION | 环境: $ENV"

# ============================================================
# 步骤 1: 查找可用快照
# ============================================================
log_info "=========================================="
log_info "步骤 1: 查找可用快照"
log_info "=========================================="

if [[ -z "$SNAPSHOT_ID" ]]; then
  log_info "查询集群 '$SOURCE_CLUSTER_ID' 的最新自动备份快照..."

  SNAPSHOT_ID=$(aws rds describe-db-cluster-snapshots \
    --db-cluster-identifier "$SOURCE_CLUSTER_ID" \
    --snapshot-type automated \
    --query 'DBClusterSnapshots | sort_by(@, &SnapshotCreateTime) | [-1].DBClusterSnapshotIdentifier' \
    --output text 2>/dev/null || echo "None")

  if [[ "$SNAPSHOT_ID" == "None" || -z "$SNAPSHOT_ID" ]]; then
    log_error "未找到集群 '$SOURCE_CLUSTER_ID' 的自动备份快照"
    log_info "请检查集群标识符是否正确，或使用 --snapshot-id 手动指定"
    exit 1
  fi
fi

# 获取快照详情
SNAPSHOT_INFO=$(aws rds describe-db-cluster-snapshots \
  --db-cluster-snapshot-identifier "$SNAPSHOT_ID" \
  --query 'DBClusterSnapshots[0].{CreateTime:SnapshotCreateTime,Status:Status,Engine:Engine,EngineVersion:EngineVersion}' \
  --output json 2>/dev/null || echo "{}")

SNAPSHOT_TIME=$(echo "$SNAPSHOT_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('CreateTime','unknown'))" 2>/dev/null || echo "unknown")
SNAPSHOT_STATUS=$(echo "$SNAPSHOT_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('Status','unknown'))" 2>/dev/null || echo "unknown")

log_info "快照 ID:    $SNAPSHOT_ID"
log_info "快照时间:   $SNAPSHOT_TIME"
log_info "快照状态:   $SNAPSHOT_STATUS"

# 计算 RPO
if [[ "$SNAPSHOT_TIME" != "unknown" ]]; then
  CURRENT_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  log_warn "RPO 评估: 快照时间 = $SNAPSHOT_TIME | 当前时间 = $CURRENT_TIME"
  log_warn "数据损失窗口: 从快照时间到故障发生时间之间的数据将丢失"
fi

# ============================================================
# 步骤 2: 安全确认
# ============================================================
log_info "=========================================="
log_info "步骤 2: 恢复计划确认"
log_info "=========================================="

echo ""
echo "================================================"
echo "  Aurora 集群恢复计划"
echo "================================================"
echo "  环境:           $ENV"
echo "  源集群:         $SOURCE_CLUSTER_ID"
echo "  快照 ID:        $SNAPSHOT_ID"
echo "  快照时间:       $SNAPSHOT_TIME"
echo "  新集群 ID:      $NEW_CLUSTER_ID"
echo "  跳过 DNS 切换:  $SKIP_DNS"
echo "================================================"
echo ""

if [[ "$DRY_RUN" == true ]]; then
  log_info "[DRY-RUN] 仅显示恢复计划，不执行实际操作"
  exit 0
fi

if [[ "$ENV" == "prod" ]]; then
  log_warn "即将在 PROD 环境执行恢复操作！"
  read -r -p "请输入 'RESTORE-PROD' 确认: " CONFIRM
  if [[ "$CONFIRM" != "RESTORE-PROD" ]]; then
    log_info "已取消操作"
    exit 0
  fi
else
  read -r -p "确认恢复? (y/N): " CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    log_info "已取消操作"
    exit 0
  fi
fi

# ============================================================
# 步骤 3: 执行恢复
# ============================================================
log_info "=========================================="
log_info "步骤 3: 从快照恢复集群"
log_info "=========================================="

# 获取源集群的 VPC 安全组和子网组
SOURCE_SG=$(aws rds describe-db-clusters \
  --db-cluster-identifier "$SOURCE_CLUSTER_ID" \
  --query 'DBClusters[0].VpcSecurityGroups[*].VpcSecurityGroupId' \
  --output text 2>/dev/null || echo "")

SOURCE_SUBNET_GROUP=$(aws rds describe-db-clusters \
  --db-cluster-identifier "$SOURCE_CLUSTER_ID" \
  --query 'DBClusters[0].DBSubnetGroup' \
  --output text 2>/dev/null || echo "")

RESTORE_CMD="aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier $NEW_CLUSTER_ID \
  --snapshot-identifier $SNAPSHOT_ID \
  --engine $DB_ENGINE \
  --vpc-security-group-ids $SOURCE_SG \
  --db-subnet-group-name $SOURCE_SUBNET_GROUP \
  --deletion-protection"

if [[ "$ENV" == "prod" ]]; then
  RESTORE_CMD="$RESTORE_CMD --storage-encrypted"
fi

log_info "执行恢复命令..."
eval "$RESTORE_CMD"

log_info "等待集群恢复完成..."
aws rds wait db-cluster-available \
  --db-cluster-identifier "$NEW_CLUSTER_ID"

log_info "集群 '$NEW_CLUSTER_ID' 恢复完成"

# ============================================================
# 步骤 4: 创建实例
# ============================================================
log_info "=========================================="
log_info "步骤 4: 创建数据库实例"
log_info "=========================================="

if [[ "$ENV" == "prod" ]]; then
  INSTANCE_CLASS="db.r6g.large"
else
  INSTANCE_CLASS="db.t3.medium"
fi

WRITER_INSTANCE_ID="${NEW_CLUSTER_ID}-writer"

aws rds create-db-instance \
  --db-instance-identifier "$WRITER_INSTANCE_ID" \
  --db-cluster-identifier "$NEW_CLUSTER_ID" \
  --db-instance-class "$INSTANCE_CLASS" \
  --engine "$DB_ENGINE" \
  --no-publicly-accessible

log_info "等待 Writer 实例就绪..."
aws rds wait db-instance-available \
  --db-instance-identifier "$WRITER_INSTANCE_ID"

log_info "Writer 实例 '$WRITER_INSTANCE_ID' 就绪"

# Prod 环境创建 Reader 实例
if [[ "$ENV" == "prod" ]]; then
  READER_INSTANCE_ID="${NEW_CLUSTER_ID}-reader"
  log_info "Prod 环境: 创建 Reader 实例..."

  aws rds create-db-instance \
    --db-instance-identifier "$READER_INSTANCE_ID" \
    --db-cluster-identifier "$NEW_CLUSTER_ID" \
    --db-instance-class "$INSTANCE_CLASS" \
    --engine "$DB_ENGINE" \
    --no-publicly-accessible

  aws rds wait db-instance-available \
    --db-instance-identifier "$READER_INSTANCE_ID"

  log_info "Reader 实例 '$READER_INSTANCE_ID' 就绪"
fi

# ============================================================
# 步骤 5: 验证连接
# ============================================================
log_info "=========================================="
log_info "步骤 5: 验证恢复结果"
log_info "=========================================="

NEW_ENDPOINT=$(aws rds describe-db-clusters \
  --db-cluster-identifier "$NEW_CLUSTER_ID" \
  --query 'DBClusters[0].Endpoint' \
  --output text)

NEW_PORT=$(aws rds describe-db-clusters \
  --db-cluster-identifier "$NEW_CLUSTER_ID" \
  --query 'DBClusters[0].Port' \
  --output text)

NEW_STATUS=$(aws rds describe-db-clusters \
  --db-cluster-identifier "$NEW_CLUSTER_ID" \
  --query 'DBClusters[0].Status' \
  --output text)

echo ""
echo "================================================"
echo "  恢复结果"
echo "================================================"
echo "  新集群 ID:     $NEW_CLUSTER_ID"
echo "  集群状态:       $NEW_STATUS"
echo "  集群端点:       $NEW_ENDPOINT"
echo "  端口:           $NEW_PORT"
echo "  实例类型:       $INSTANCE_CLASS"
echo "================================================"
echo ""

# ============================================================
# 步骤 6: DNS/CNAME 切换 (可选)
# ============================================================
if [[ "$SKIP_DNS" == false ]]; then
  log_info "=========================================="
  log_info "步骤 6: DNS/CNAME 切换"
  log_info "=========================================="

  log_warn "自动 DNS 切换未实现，请手动执行以下操作:"
  echo ""
  echo "  1. 更新应用配置中的数据库端点为: $NEW_ENDPOINT"
  echo "  2. 如使用 Route 53 CNAME，请更新记录指向新端点"
  echo "  3. 重启应用服务以使用新的数据库连接"
  echo "  4. 验证应用正常访问数据库"
  echo "  5. 确认无误后，可删除旧集群 (需先禁用删除保护):"
  echo "     aws rds modify-db-cluster --db-cluster-identifier $SOURCE_CLUSTER_ID --no-deletion-protection"
  echo "     aws rds delete-db-cluster --db-cluster-identifier $SOURCE_CLUSTER_ID --skip-final-snapshot"
  echo ""
fi

# ============================================================
# 恢复摘要
# ============================================================
log_info "=========================================="
log_info "恢复完成摘要"
log_info "=========================================="
log_info "快照时间:       $SNAPSHOT_TIME"
log_info "恢复完成时间:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
log_info "新集群端点:     $NEW_ENDPOINT:$NEW_PORT"
log_warn "请尽快验证数据完整性并完成 DNS 切换"
