import { memo } from 'react';

import { Card } from '@/shared/ui';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/formatDate';

import { AGENT_STATUS_CONFIG } from '../model/constants';
import type { Agent } from '../model/types';

interface AgentCardProps {
  agent: Agent;
  onClick?: () => void;
}

// memo: AgentList 中的列表项，筛选/分页操作时未变化的卡片跳过重渲染
export const AgentCard = memo(function AgentCard({ agent, onClick }: AgentCardProps) {
  const status = AGENT_STATUS_CONFIG[agent.status];
  const isClickable = !!onClick;

  // 可点击时渲染 button，否则渲染 div — 避免无意义的空 button 破坏语义化
  const Wrapper = isClickable ? 'button' : 'div';
  const wrapperProps = isClickable
    ? { type: 'button' as const, onClick, 'aria-label': `查看 Agent: ${agent.name}` }
    : {};

  return (
    <Card className={cn('transition-shadow', isClickable && 'cursor-pointer hover:shadow-md')}>
      <Wrapper className="w-full text-left" {...wrapperProps}>
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
          <span>创建于 {formatDate(agent.created_at)}</span>
        </div>
      </Wrapper>
    </Card>
  );
});
