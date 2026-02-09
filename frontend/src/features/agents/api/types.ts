import type { Agent } from '@/entities/agent';
import type { PageResponse } from '@/shared/types';

export interface CreateAgentRequest {
  name: string;
  description?: string;
  system_prompt?: string;
  model_id?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  system_prompt?: string;
  model_id?: string;
  temperature?: number;
  max_tokens?: number;
}

export type AgentListResponse = PageResponse<Agent>;
