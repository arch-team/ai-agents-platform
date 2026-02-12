// Team Execution 状态徽章

import { cn } from '@/shared/lib/cn';

import type { TeamExecutionStatus } from '../api/types';

interface TeamExecStatusBadgeProps {
  status: TeamExecutionStatus;
}

const statusConfig: Record<TeamExecutionStatus, { label: string; className: string }> = {
  pending: { label: '等待中', className: 'bg-yellow-100 text-yellow-800' },
  running: { label: '运行中', className: 'bg-blue-100 text-blue-800' },
  completed: { label: '已完成', className: 'bg-green-100 text-green-800' },
  failed: { label: '失败', className: 'bg-red-100 text-red-800' },
  cancelled: { label: '已取消', className: 'bg-gray-100 text-gray-800' },
};

export function TeamExecStatusBadge({ status }: TeamExecStatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        config.className,
      )}
    >
      {status === 'running' && (
        <span className="mr-1.5 h-2 w-2 animate-pulse rounded-full bg-blue-500" aria-hidden="true" />
      )}
      {config.label}
    </span>
  );
}
