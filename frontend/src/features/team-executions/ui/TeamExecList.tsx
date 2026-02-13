// Team Execution 列表

import { cn } from '@/shared/lib/cn';
import { formatDateTime } from '@/shared/lib/formatDate';
import { Spinner, ErrorMessage } from '@/shared/ui';

import type { TeamExecution } from '../api/types';
import { useTeamExecutions } from '../api/queries';

import { TeamExecStatusBadge } from './TeamExecStatusBadge';

interface TeamExecListProps {
  selectedId: number | null;
  onSelect: (execution: TeamExecution) => void;
}

export function TeamExecList({ selectedId, onSelect }: TeamExecListProps) {
  const { data, isLoading, error } = useTeamExecutions();

  if (isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error="加载执行列表失败" />;
  }

  if (!data?.items.length) {
    return (
      <div className="py-8 text-center text-sm text-gray-500">
        暂无执行记录，创建第一个 Team Execution 开始使用
      </div>
    );
  }

  return (
    <ul className="divide-y divide-gray-100" role="list" aria-label="执行列表">
      {data.items.map((execution) => (
        <li key={execution.id}>
          <button
            type="button"
            onClick={() => onSelect(execution)}
            className={cn(
              'flex w-full items-center justify-between px-4 py-3 text-left transition-colors',
              'hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500',
              selectedId === execution.id && 'bg-blue-50',
            )}
            aria-current={selectedId === execution.id ? 'true' : undefined}
          >
            <div className="min-w-0 flex-1">
              {/* CSS truncate 自动处理文本溢出，无需手动截断 */}
              <p className="truncate text-sm font-medium text-gray-900">
                {execution.prompt}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                #{execution.id} · {formatDateTime(execution.created_at)}
              </p>
            </div>
            <div className="ml-3 shrink-0">
              <TeamExecStatusBadge status={execution.status} />
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
