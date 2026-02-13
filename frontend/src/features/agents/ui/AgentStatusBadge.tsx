// Agent 状态徽章组件
import { StatusBadge } from '@/shared/ui';
import { AGENT_STATUS_CONFIG } from '@/entities/agent';
import type { AgentStatus } from '@/entities/agent';

interface AgentStatusBadgeProps {
  status: AgentStatus;
  className?: string;
}

export function AgentStatusBadge({ status, className }: AgentStatusBadgeProps) {
  return <StatusBadge status={status} config={AGENT_STATUS_CONFIG} className={className} />;
}
