// Builder API 请求/响应类型

export interface AgentConfig {
  name: string;
  description: string;
  system_prompt: string;
  model_id: string;
  temperature: number;
  max_tokens: number;
}

export interface BuilderSession {
  id: number;
  user_id: number;
  prompt: string;
  status: 'pending' | 'generating' | 'confirmed' | 'cancelled';
  generated_config: AgentConfig | null;
  agent_name: string | null;
  created_agent_id: number | null;
  created_at: string;
  updated_at: string;
}

// SSE 流式数据块类型
export interface BuilderStreamChunk {
  content?: string;
  config?: AgentConfig;
  done?: boolean;
  error?: string;
}

export interface CreateBuilderSessionRequest {
  prompt: string;
}

export interface ConfirmBuilderSessionResponse {
  id: number;
  created_agent_id: number;
  status: 'confirmed';
  updated_at: string;
}
