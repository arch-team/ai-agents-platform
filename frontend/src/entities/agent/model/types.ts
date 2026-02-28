export interface AgentConfig {
  model_id: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  enable_memory: boolean;
}

export type AgentStatus = 'draft' | 'active' | 'archived';

export interface Agent {
  id: number;
  name: string;
  description: string;
  system_prompt: string;
  status: AgentStatus;
  owner_id: number;
  config: AgentConfig;
  tool_ids: number[];
  created_at: string;
  updated_at: string;
}
