// Builder Zustand store 类型定义

import type { AgentConfig } from '../api/types';

export interface BuilderState {
  /** 当前 Builder 会话 ID */
  sessionId: number | null;
  /** SSE 流式累积的文本内容 */
  streamContent: string;
  /** 从 SSE 流中解析出的 Agent 配置 */
  generatedConfig: AgentConfig | null;
  /** 是否正在生成中（SSE 连接中） */
  isGenerating: boolean;
  /** 是否正在确认创建 Agent */
  isConfirming: boolean;
  /** 错误信息 */
  error: string | null;

  // Actions
  setSessionId: (id: number | null) => void;
  appendStreamContent: (content: string) => void;
  setGeneratedConfig: (config: AgentConfig | null) => void;
  setGenerating: (generating: boolean) => void;
  setConfirming: (confirming: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}
