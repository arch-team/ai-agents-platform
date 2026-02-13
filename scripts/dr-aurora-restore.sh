#!/bin/bash
# =============================================================================
# Aurora 快照恢复验证脚本
# =============================================================================
# 用途: 在 Dev 环境验证 Aurora MySQL 快照恢复流程
# 前提: 已配置 AWS CLI + 拥有 RDS 所需 IAM 权限
# 使用: ./scripts/dr-aurora-restore.sh [环境名称] [集群标识符]
#
# 参数:
#   $1 - 环境名称 (默认: dev)
#   $2 - Aurora 集群标识符 (可选，自动检测)
#
# 示例:
#   ./scripts/dr-aurora-restore.sh dev
#   ./scripts/dr-aurora-restore.sh dev my-cluster-id
# =============================================================================

set -euo pipefail

# --- 配置 ---
ENV="${1:-dev}"
CLUSTER_ID="${2:-}"
RESTORE_SUFFIX="dr-test-$(date +%Y%m%d%H%M%S)"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
WAIT_TIMEOUT=1800  # 等待超时时间 (秒)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 无颜色

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- 安全检查 ---
if [[ "$ENV" == "prod" ]]; then
  log_warn "检测到 Prod 环境！快照恢复验证应在 Dev 环境执行。"
  read -r -p "确定要在 Prod 环境执行吗？(输入 YES 确认): " confirm
  if [[ "$confirm" != "YES" ]]; then
    log_info "已取消操作。"
    exit 0
  fi
fi

echo "============================================"
echo " Aurora 快照恢复验证 (${ENV})"
echo " 区域: ${REGION}"
echo " 时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================"

# --- 步骤 1: 自动检测集群标识符 ---
if [[ -z "$CLUSTER_ID" ]]; then
  log_info "1. 自动检测 Aurora 集群标识符..."
  CLUSTER_ID=$(aws rds describe-db-clusters \
    --region "$REGION" \
    --query "DBClusters[?contains(DBClusterIdentifier, 'database-${ENV}')].DBClusterIdentifier | [0]" \
    --output text 2>/dev/null || true)

  if [[ -z "$CLUSTER_ID" || "$CLUSTER_ID" == "None" ]]; then
    log_error "未找到匹配 'database-${ENV}' 的 Aurora 集群。"
    log_info "请手动指定集群标识符: $0 ${ENV} <cluster-id>"
    exit 1
  fi
  log_info "   检测到集群: ${CLUSTER_ID}"
else
  log_info "1. 使用指定集群: ${CLUSTER_ID}"
fi

RESTORE_CLUSTER_ID="${CLUSTER_ID}-${RESTORE_SUFFIX}"
RESTORE_INSTANCE_ID="${RESTORE_CLUSTER_ID}-writer"

# --- 步骤 2: 获取最新自动快照 ---
log_info "2. 获取最新自动快照..."
SNAPSHOT=$(aws rds describe-db-cluster-snapshots \
  --region "$REGION" \
  --db-cluster-identifier "$CLUSTER_ID" \
  --snapshot-type automated \
  --query 'DBClusterSnapshots | sort_by(@, &SnapshotCreateTime) | [-1].DBClusterSnapshotIdentifier' \
  --output text)

if [[ -z "$SNAPSHOT" || "$SNAPSHOT" == "None" ]]; then
  log_error "未找到集群 ${CLUSTER_ID} 的自动快照。"
  exit 1
fi

SNAPSHOT_TIME=$(aws rds describe-db-cluster-snapshots \
  --region "$REGION" \
  --db-cluster-snapshot-identifier "$SNAPSHOT" \
  --query 'DBClusterSnapshots[0].SnapshotCreateTime' \
  --output text)

log_info "   快照: ${SNAPSHOT}"
log_info "   创建时间: ${SNAPSHOT_TIME}"

# --- 步骤 3: 获取原集群配置 ---
log_info "3. 读取原集群网络配置..."
SUBNET_GROUP=$(aws rds describe-db-clusters \
  --region "$REGION" \
  --db-cluster-identifier "$CLUSTER_ID" \
  --query 'DBClusters[0].DBSubnetGroupName' \
  --output text)

VPC_SECURITY_GROUPS=$(aws rds describe-db-clusters \
  --region "$REGION" \
  --db-cluster-identifier "$CLUSTER_ID" \
  --query 'DBClusters[0].VpcSecurityGroups[*].VpcSecurityGroupId' \
  --output text | tr '\t' ',')

log_info "   子网组: ${SUBNET_GROUP}"
log_info "   安全组: ${VPC_SECURITY_GROUPS}"

# --- 步骤 4: 从快照恢复集群 ---
log_info "4. 从快照恢复新集群: ${RESTORE_CLUSTER_ID}"
START_TIME=$(date +%s)

aws rds restore-db-cluster-from-snapshot \
  --region "$REGION" \
  --db-cluster-identifier "$RESTORE_CLUSTER_ID" \
  --snapshot-identifier "$SNAPSHOT" \
  --engine aurora-mysql \
  --db-subnet-group-name "$SUBNET_GROUP" \
  --vpc-security-group-ids ${VPC_SECURITY_GROUPS//,/ } \
  --tags "Key=Purpose,Value=DR-Test" "Key=Environment,Value=${ENV}" "Key=AutoCleanup,Value=true"

log_info "   集群恢复已发起，等待可用..."

# --- 步骤 5: 等待集群可用 ---
log_info "5. 等待集群可用 (超时: ${WAIT_TIMEOUT}s)..."
aws rds wait db-cluster-available \
  --region "$REGION" \
  --db-cluster-identifier "$RESTORE_CLUSTER_ID" \
  2>/dev/null || {
    log_error "等待集群可用超时。请手动检查集群状态。"
    log_warn "清理命令: aws rds delete-db-cluster --db-cluster-identifier ${RESTORE_CLUSTER_ID} --skip-final-snapshot --region ${REGION}"
    exit 1
  }

log_info "   集群已可用。"

# --- 步骤 6: 创建数据库实例 ---
log_info "6. 创建数据库实例: ${RESTORE_INSTANCE_ID}"
aws rds create-db-instance \
  --region "$REGION" \
  --db-instance-identifier "$RESTORE_INSTANCE_ID" \
  --db-cluster-identifier "$RESTORE_CLUSTER_ID" \
  --db-instance-class "db.t3.medium" \
  --engine aurora-mysql \
  --tags "Key=Purpose,Value=DR-Test" "Key=Environment,Value=${ENV}" "Key=AutoCleanup,Value=true"

log_info "   等待实例可用..."
aws rds wait db-instance-available \
  --region "$REGION" \
  --db-instance-identifier "$RESTORE_INSTANCE_ID" \
  2>/dev/null || {
    log_error "等待实例可用超时。"
    log_warn "请手动清理资源。"
    exit 1
  }

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

log_info "   实例已可用。恢复耗时: ${ELAPSED} 秒"

# --- 步骤 7: 验证恢复的集群 ---
log_info "7. 验证恢复的集群..."
RESTORE_ENDPOINT=$(aws rds describe-db-clusters \
  --region "$REGION" \
  --db-cluster-identifier "$RESTORE_CLUSTER_ID" \
  --query 'DBClusters[0].Endpoint' \
  --output text)

RESTORE_STATUS=$(aws rds describe-db-clusters \
  --region "$REGION" \
  --db-cluster-identifier "$RESTORE_CLUSTER_ID" \
  --query 'DBClusters[0].Status' \
  --output text)

log_info "   端点: ${RESTORE_ENDPOINT}"
log_info "   状态: ${RESTORE_STATUS}"

if [[ "$RESTORE_STATUS" == "available" ]]; then
  log_info "   集群恢复验证通过!"
else
  log_error "   集群状态异常: ${RESTORE_STATUS}"
fi

# --- 步骤 8: 清理测试资源 ---
log_info "8. 清理测试资源..."
log_info "   删除实例: ${RESTORE_INSTANCE_ID}"
aws rds delete-db-instance \
  --region "$REGION" \
  --db-instance-identifier "$RESTORE_INSTANCE_ID" \
  --skip-final-snapshot \
  2>/dev/null || log_warn "   删除实例失败，可能需要手动清理。"

log_info "   等待实例删除..."
aws rds wait db-instance-deleted \
  --region "$REGION" \
  --db-instance-identifier "$RESTORE_INSTANCE_ID" \
  2>/dev/null || log_warn "   等待实例删除超时，请手动确认。"

log_info "   删除集群: ${RESTORE_CLUSTER_ID}"
aws rds delete-db-cluster \
  --region "$REGION" \
  --db-cluster-identifier "$RESTORE_CLUSTER_ID" \
  --skip-final-snapshot \
  2>/dev/null || log_warn "   删除集群失败，可能需要手动清理。"

# --- 结果汇总 ---
echo ""
echo "============================================"
echo " Aurora 快照恢复验证完成"
echo "============================================"
echo " 环境:       ${ENV}"
echo " 源集群:     ${CLUSTER_ID}"
echo " 快照:       ${SNAPSHOT}"
echo " 快照时间:   ${SNAPSHOT_TIME}"
echo " 恢复耗时:   ${ELAPSED} 秒"
echo " RTO 目标:   < 900 秒 (15 分钟)"
if [[ $ELAPSED -lt 900 ]]; then
  echo -e " RTO 结果:   ${GREEN}通过${NC} (${ELAPSED}s < 900s)"
else
  echo -e " RTO 结果:   ${RED}未通过${NC} (${ELAPSED}s >= 900s)"
fi
echo "============================================"
