import type { Agent } from '@/entities/agent';
import type { PageResponse } from '@/shared/types';

export interface CreateAgentRequest {
  name: string;
  description?: string;
  system_prompt?: string;
  model_id?: string;
  temperature?: number;
  max_tokens?: number;
  tool_ids?: number[];
  enable_memory?: boolean;
}

export type UpdateAgentRequest = Partial<CreateAgentRequest>;

export type AgentListResponse = PageResponse<Agent>;

export interface AgentPreviewResponse {
  content: string;
  model_id: string;
  tokens_input: number;
  tokens_output: number;
}
