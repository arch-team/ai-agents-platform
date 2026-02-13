// 模板状态徽章组件
import { cn } from '@/shared/lib/cn';

import type { TemplateStatus } from '../api/types';

const STATUS_CONFIG: Record<TemplateStatus, { label: string; className: string }> = {
  draft: {
    label: '草稿',
    className: 'bg-gray-100 text-gray-800',
  },
  published: {
    label: '已发布',
    className: 'bg-green-100 text-green-800',
  },
  archived: {
    label: '已归档',
    className: 'bg-yellow-100 text-yellow-800',
  },
};

interface TemplateStatusBadgeProps {
  status: TemplateStatus;
  className?: string;
}

export function TemplateStatusBadge({ status, className }: TemplateStatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        config.className,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
