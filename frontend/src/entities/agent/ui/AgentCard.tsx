import { Card } from '@/shared/ui';
import { cn } from '@/shared/lib/cn';

import type { Agent, AgentStatus } from '../model/types';

interface AgentCardProps {
  agent: Agent;
  onClick?: () => void;
}

const statusStyles: Record<AgentStatus, { label: string; className: string }> = {
  draft: { label: '草稿', className: 'bg-gray-100 text-gray-700' },
  active: { label: '活跃', className: 'bg-green-100 text-green-700' },
  archived: { label: '已归档', className: 'bg-yellow-100 text-yellow-700' },
};

export function AgentCard({ agent, onClick }: AgentCardProps) {
  const status = statusStyles[agent.status];
  const formattedDate = new Date(agent.created_at).toLocaleDateString('zh-CN');

  return (
    <Card className={cn('transition-shadow', onClick && 'cursor-pointer hover:shadow-md')}>
      <button
        type="button"
        className="w-full text-left"
        onClick={onClick}
        aria-label={`查看 Agent: ${agent.name}`}
      >
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-lg font-semibold text-gray-900">{agent.name}</h3>
            <p className="mt-1 line-clamp-2 text-sm text-gray-500">{agent.description}</p>
          </div>
          <span
            className={cn(
              'ml-3 inline-flex shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium',
              status.className,
            )}
          >
            {status.label}
          </span>
        </div>
        <div className="mt-4 text-xs text-gray-400">
          <span>创建于 {formattedDate}</span>
        </div>
      </button>
    </Card>
  );
}
