// Team Execution 相关类型定义

export type TeamExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface TeamExecution {
  id: number;
  agent_id: number;
  user_id: number;
  prompt: string;
  status: TeamExecutionStatus;
  result: string | null;
  error_message: string | null;
  conversation_id: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeamExecutionLog {
  id: number;
  execution_id: number;
  sequence: number;
  log_type: string;
  content: string;
  created_at: string;
}

export interface TeamExecutionSSEChunk {
  id?: number;
  sequence?: number;
  content: string;
  log_type?: string;
  done?: boolean;
  error?: string;
}

export interface CreateTeamExecutionDTO {
  agent_id: number;
  prompt: string;
}
