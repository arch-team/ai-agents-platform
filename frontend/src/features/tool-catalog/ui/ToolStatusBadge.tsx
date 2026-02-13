// 工具状态标签组件
import { StatusBadge } from '@/shared/ui';

import type { ToolStatus } from '../api/types';

const STATUS_CONFIG: Record<ToolStatus, { label: string; className: string }> = {
  DRAFT: { label: '草稿', className: 'bg-gray-100 text-gray-700' },
  PENDING_REVIEW: { label: '待审批', className: 'bg-yellow-100 text-yellow-700' },
  APPROVED: { label: '已审批', className: 'bg-green-100 text-green-700' },
  REJECTED: { label: '已拒绝', className: 'bg-red-100 text-red-700' },
  DEPRECATED: { label: '已废弃', className: 'bg-orange-100 text-orange-700' },
};

interface ToolStatusBadgeProps {
  status: ToolStatus;
  className?: string;
}

export function ToolStatusBadge({ status, className }: ToolStatusBadgeProps) {
  return <StatusBadge status={status} config={STATUS_CONFIG} className={className} />;
}
