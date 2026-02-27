// Team Execution Store 类型定义

export interface StreamLogEntry {
  sequence: number;
  content: string;
  logType: string;
}

export interface TeamExecState {
  selectedExecutionId: number | null;
  streamLogs: StreamLogEntry[];
  isStreaming: boolean;
  error: string | null;
  setSelectedExecution: (id: number | null) => void;
  appendLog: (entry: StreamLogEntry) => void;
  clearLogs: () => void;
  setStreaming: (streaming: boolean) => void;
  setError: (error: string) => void;
  clearError: () => void;
}
