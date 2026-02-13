// 模板状态徽章组件
import { StatusBadge } from '@/shared/ui';

import type { TemplateStatus } from '../api/types';

const STATUS_CONFIG: Record<TemplateStatus, { label: string; className: string }> = {
  draft: { label: '草稿', className: 'bg-gray-100 text-gray-800' },
  published: { label: '已发布', className: 'bg-green-100 text-green-800' },
  archived: { label: '已归档', className: 'bg-yellow-100 text-yellow-800' },
};

interface TemplateStatusBadgeProps {
  status: TemplateStatus;
  className?: string;
}

export function TemplateStatusBadge({ status, className }: TemplateStatusBadgeProps) {
  return <StatusBadge status={status} config={STATUS_CONFIG} className={className} />;
}
