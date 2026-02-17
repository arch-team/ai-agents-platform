// Team Execution 状态徽章 — 基于共享 StatusBadge 组件
// running 状态带脉动动画指示器

import { StatusBadge } from '@/shared/ui';

import type { TeamExecutionStatus } from '../api/types';

const STATUS_CONFIG: Record<TeamExecutionStatus, { label: string; className: string }> = {
  pending: { label: '等待中', className: 'bg-yellow-100 text-yellow-800' },
  running: { label: '运行中', className: 'bg-blue-100 text-blue-800' },
  completed: { label: '已完成', className: 'bg-green-100 text-green-800' },
  failed: { label: '失败', className: 'bg-red-100 text-red-800' },
  cancelled: { label: '已取消', className: 'bg-gray-100 text-gray-800' },
};

interface TeamExecStatusBadgeProps {
  status: TeamExecutionStatus;
  className?: string;
}

export function TeamExecStatusBadge({ status, className }: TeamExecStatusBadgeProps) {
  return (
    <StatusBadge
      status={status}
      config={STATUS_CONFIG}
      className={className}
      prefix={
        status === 'running' ? (
          <span className="mr-1.5 h-2 w-2 animate-pulse rounded-full bg-blue-500" aria-hidden="true" />
        ) : undefined
      }
    />
  );
}
