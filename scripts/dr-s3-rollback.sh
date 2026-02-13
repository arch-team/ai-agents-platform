#!/bin/bash
# =============================================================================
# S3 版本回滚验证脚本
# =============================================================================
# 用途: 验证 S3 版本控制下的对象回滚能力
# 前提: 已配置 AWS CLI + 拥有 S3 所需 IAM 权限 + Bucket 已启用版本控制
# 使用: ./scripts/dr-s3-rollback.sh [bucket名称]
#
# 参数:
#   $1 - S3 Bucket 名称 (默认: ai-agents-platform-knowledge-dev)
#
# 示例:
#   ./scripts/dr-s3-rollback.sh
#   ./scripts/dr-s3-rollback.sh ai-agents-platform-knowledge-dev
# =============================================================================

set -euo pipefail

# --- 配置 ---
BUCKET="${1:-ai-agents-platform-knowledge-dev}"
TEST_PREFIX="dr-test"
TEST_KEY="${TEST_PREFIX}/test-document.txt"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
PASSED=0
FAILED=0

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_pass()  { echo -e "${GREEN}[PASS]${NC} $*"; ((PASSED++)); }
log_fail()  { echo -e "${RED}[FAIL]${NC} $*"; ((FAILED++)); }

# 清理函数 — 确保测试资源被删除
cleanup() {
  log_info "清理测试资源..."

  # 删除所有版本 (包括删除标记)
  local versions
  versions=$(aws s3api list-object-versions \
    --region "$REGION" \
    --bucket "$BUCKET" \
    --prefix "$TEST_PREFIX/" \
    --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}, DeleteMarkers: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
    --output json 2>/dev/null || echo '{"Objects":null,"DeleteMarkers":null}')

  # 删除所有版本
  local objects
  objects=$(echo "$versions" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = []
if data.get('Objects'):
    items.extend(data['Objects'])
if data.get('DeleteMarkers'):
    items.extend(data['DeleteMarkers'])
if items:
    print(json.dumps({'Objects': items, 'Quiet': True}))
else:
    print('')
" 2>/dev/null || echo "")

  if [[ -n "$objects" ]]; then
    echo "$objects" | aws s3api delete-objects \
      --region "$REGION" \
      --bucket "$BUCKET" \
      --delete file:///dev/stdin \
      > /dev/null 2>&1 || log_warn "部分清理失败，请手动检查 s3://${BUCKET}/${TEST_PREFIX}/"
  fi

  log_info "清理完成。"
}

# 注册退出清理
trap cleanup EXIT

echo "============================================"
echo " S3 版本回滚验证"
echo "============================================"
echo " Bucket: ${BUCKET}"
echo " 区域:   ${REGION}"
echo " 时间:   $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================"

# --- 步骤 0: 前置检查 ---
log_info "0. 前置检查..."

# 检查 Bucket 是否存在
if ! aws s3api head-bucket --bucket "$BUCKET" --region "$REGION" 2>/dev/null; then
  log_error "Bucket 不存在或无访问权限: ${BUCKET}"
  exit 1
fi

# 检查版本控制是否启用
VERSIONING=$(aws s3api get-bucket-versioning \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --query 'Status' \
  --output text)

if [[ "$VERSIONING" != "Enabled" ]]; then
  log_error "Bucket 版本控制未启用 (当前状态: ${VERSIONING})"
  exit 1
fi

log_info "   版本控制: 已启用"

# --- 测试 1: 版本覆盖与回滚 ---
echo ""
log_info "=== 测试 1: 版本覆盖与回滚 ==="

# 上传初始版本 (v1)
log_info "1a. 上传初始版本 (v1)..."
V1_CONTENT="版本-1: 初始文档内容 ($(date -u '+%Y-%m-%dT%H:%M:%SZ'))"
V1_RESULT=$(echo "$V1_CONTENT" | aws s3api put-object \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --key "$TEST_KEY" \
  --body /dev/stdin \
  --query 'VersionId' \
  --output text)
log_info "   v1 版本 ID: ${V1_RESULT}"

# 上传新版本 (v2) — 模拟覆盖
log_info "1b. 上传新版本覆盖 (v2)..."
V2_CONTENT="版本-2: 覆盖后的文档内容 ($(date -u '+%Y-%m-%dT%H:%M:%SZ'))"
V2_RESULT=$(echo "$V2_CONTENT" | aws s3api put-object \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --key "$TEST_KEY" \
  --body /dev/stdin \
  --query 'VersionId' \
  --output text)
log_info "   v2 版本 ID: ${V2_RESULT}"

# 验证当前版本是 v2
log_info "1c. 验证当前版本..."
CURRENT_CONTENT=$(aws s3 cp "s3://${BUCKET}/${TEST_KEY}" - --region "$REGION" 2>/dev/null)
if [[ "$CURRENT_CONTENT" == "$V2_CONTENT" ]]; then
  log_pass "当前版本确认为 v2"
else
  log_fail "当前版本不是预期的 v2"
fi

# 列出版本历史
log_info "1d. 列出版本历史..."
aws s3api list-object-versions \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --prefix "$TEST_KEY" \
  --query 'Versions[].{VersionId:VersionId,LastModified:LastModified,IsLatest:IsLatest}' \
  --output table

# 回滚: 将 v1 复制为当前版本
log_info "1e. 回滚到 v1..."
aws s3api copy-object \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --copy-source "${BUCKET}/${TEST_KEY}?versionId=${V1_RESULT}" \
  --key "$TEST_KEY" \
  > /dev/null

# 验证回滚结果
ROLLBACK_CONTENT=$(aws s3 cp "s3://${BUCKET}/${TEST_KEY}" - --region "$REGION" 2>/dev/null)
if [[ "$ROLLBACK_CONTENT" == "$V1_CONTENT" ]]; then
  log_pass "回滚验证通过 — 内容已恢复到 v1"
else
  log_fail "回滚验证失败 — 内容不匹配"
  log_error "   期望: ${V1_CONTENT}"
  log_error "   实际: ${ROLLBACK_CONTENT}"
fi

# --- 测试 2: 删除与恢复 ---
echo ""
log_info "=== 测试 2: 删除与恢复 ==="

DELETE_KEY="${TEST_PREFIX}/delete-test.txt"
DELETE_CONTENT="待删除的测试文档 ($(date -u '+%Y-%m-%dT%H:%M:%SZ'))"

# 上传文件
log_info "2a. 上传测试文件..."
echo "$DELETE_CONTENT" | aws s3api put-object \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --key "$DELETE_KEY" \
  --body /dev/stdin \
  > /dev/null

# 删除文件 (创建删除标记)
log_info "2b. 删除文件..."
aws s3 rm "s3://${BUCKET}/${DELETE_KEY}" --region "$REGION" > /dev/null 2>&1

# 确认文件已"删除"
if ! aws s3api head-object --bucket "$BUCKET" --key "$DELETE_KEY" --region "$REGION" 2>/dev/null; then
  log_pass "文件已删除 (返回 404)"
else
  log_fail "文件删除后仍然可访问"
fi

# 查找删除标记
log_info "2c. 查找删除标记..."
DELETE_MARKER_ID=$(aws s3api list-object-versions \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --prefix "$DELETE_KEY" \
  --query 'DeleteMarkers[?IsLatest==`true`].VersionId | [0]' \
  --output text)

if [[ -n "$DELETE_MARKER_ID" && "$DELETE_MARKER_ID" != "None" ]]; then
  log_info "   删除标记版本 ID: ${DELETE_MARKER_ID}"

  # 移除删除标记恢复文件
  log_info "2d. 移除删除标记恢复文件..."
  aws s3api delete-object \
    --region "$REGION" \
    --bucket "$BUCKET" \
    --key "$DELETE_KEY" \
    --version-id "$DELETE_MARKER_ID" \
    > /dev/null

  # 验证文件已恢复
  RESTORED_CONTENT=$(aws s3 cp "s3://${BUCKET}/${DELETE_KEY}" - --region "$REGION" 2>/dev/null || echo "")
  if [[ "$RESTORED_CONTENT" == "$DELETE_CONTENT" ]]; then
    log_pass "文件恢复验证通过 — 删除标记移除后文件已恢复"
  else
    log_fail "文件恢复验证失败 — 内容不匹配"
  fi
else
  log_fail "未找到删除标记"
fi

# --- 测试 3: 批量版本列举 ---
echo ""
log_info "=== 测试 3: 批量版本列举 ==="

log_info "3a. 列举 ${TEST_PREFIX}/ 下所有版本..."
TOTAL_VERSIONS=$(aws s3api list-object-versions \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --prefix "${TEST_PREFIX}/" \
  --query 'length(Versions || `[]`)' \
  --output text)

TOTAL_DELETE_MARKERS=$(aws s3api list-object-versions \
  --region "$REGION" \
  --bucket "$BUCKET" \
  --prefix "${TEST_PREFIX}/" \
  --query 'length(DeleteMarkers || `[]`)' \
  --output text)

log_info "   对象版本数: ${TOTAL_VERSIONS}"
log_info "   删除标记数: ${TOTAL_DELETE_MARKERS}"

if [[ "$TOTAL_VERSIONS" -gt 0 ]]; then
  log_pass "版本列举正常"
else
  log_fail "未找到任何版本"
fi

# --- 结果汇总 ---
echo ""
echo "============================================"
echo " S3 版本回滚验证完成"
echo "============================================"
echo " Bucket:   ${BUCKET}"
echo " 通过:     ${PASSED}"
echo " 失败:     ${FAILED}"
if [[ $FAILED -eq 0 ]]; then
  echo -e " 结果:     ${GREEN}全部通过${NC}"
else
  echo -e " 结果:     ${RED}有 ${FAILED} 项失败${NC}"
fi
echo "============================================"

# 返回退出码
if [[ $FAILED -gt 0 ]]; then
  exit 1
fi
