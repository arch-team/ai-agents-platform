export interface AgentConfig {
  model_id: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
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
  created_at: string;
  updated_at: string;
}
