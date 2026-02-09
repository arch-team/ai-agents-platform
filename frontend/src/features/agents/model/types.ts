import type { AgentStatus } from '@/entities/agent';

export interface AgentFilters {
  status?: AgentStatus;
  page?: number;
  page_size?: number;
}
