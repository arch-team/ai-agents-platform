// 测试集状态徽章组件

import { cn } from '@/shared/lib/cn';

import type { TestSuiteStatus } from '../api/types';

const STATUS_CONFIG: Record<TestSuiteStatus, { label: string; className: string }> = {
  draft: { label: '草稿', className: 'bg-gray-100 text-gray-700' },
  active: { label: '已激活', className: 'bg-green-100 text-green-700' },
  archived: { label: '已归档', className: 'bg-yellow-100 text-yellow-700' },
};

interface TestSuiteStatusBadgeProps {
  status: TestSuiteStatus;
  className?: string;
}

export function TestSuiteStatusBadge({ status, className }: TestSuiteStatusBadgeProps) {
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
