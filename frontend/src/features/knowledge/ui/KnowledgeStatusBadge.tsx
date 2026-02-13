// 知识库状态徽章组件
import { StatusBadge } from '@/shared/ui';

import type { KnowledgeBaseStatus } from '../api/types';

const STATUS_CONFIG: Record<KnowledgeBaseStatus, { label: string; className: string }> = {
  CREATING: { label: '创建中', className: 'bg-yellow-100 text-yellow-800' },
  ACTIVE: { label: '已激活', className: 'bg-green-100 text-green-800' },
  SYNCING: { label: '同步中', className: 'bg-blue-100 text-blue-800' },
  FAILED: { label: '失败', className: 'bg-red-100 text-red-800' },
};

interface KnowledgeStatusBadgeProps {
  status: KnowledgeBaseStatus;
  className?: string;
}

export function KnowledgeStatusBadge({ status, className }: KnowledgeStatusBadgeProps) {
  return <StatusBadge status={status} config={STATUS_CONFIG} className={className} />;
}
