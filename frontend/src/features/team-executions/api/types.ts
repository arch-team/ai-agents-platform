// Team Execution 相关类型定义

export type TeamExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface TeamExecution {
  id: number;
  agent_id: number;
  user_id: number;
  prompt: string;
  status: TeamExecutionStatus;
  result: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeamExecutionLog {
  id: number;
  execution_id: number;
  sequence: number;
  agent_name: string;
  content: string;
  created_at: string;
}

export interface TeamExecutionSSEChunk {
  id?: number;
  sequence?: number;
  content: string;
  agent_name?: string;
  done?: boolean;
  error?: string;
}

export interface CreateTeamExecutionDTO {
  agent_id: number;
  prompt: string;
}
