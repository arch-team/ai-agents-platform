// Builder Zustand store 类型定义

import type {
  AgentConfig,
  BlueprintConfigOverrides,
  BuilderPhase,
  ChatMessage,
  GeneratedBlueprint,
} from '../api/types';

export interface BuilderState {
  // ── V1 状态 (保留兼容) ──
  sessionId: number | null;
  streamContent: string;
  generatedConfig: AgentConfig | null;
  isGenerating: boolean;
  isConfirming: boolean;
  error: string | null;

  // ── V2 Blueprint 状态 ──
  phase: BuilderPhase;
  messages: ChatMessage[];
  generatedBlueprint: GeneratedBlueprint | null;
  configOverrides: BlueprintConfigOverrides;
  createdAgentId: number | null;

  // ── V1 Actions ──
  setSessionId: (id: number | null) => void;
  appendStreamContent: (content: string) => void;
  setGeneratedConfig: (config: AgentConfig | null) => void;
  setGenerating: (generating: boolean) => void;
  setConfirming: (confirming: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;

  // ── V2 Actions ──
  setPhase: (phase: BuilderPhase) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setGeneratedBlueprint: (blueprint: GeneratedBlueprint | null) => void;
  setCreatedAgentId: (id: number | null) => void;
  setConfigOverrides: (overrides: Partial<BlueprintConfigOverrides>) => void;
  resetStream: () => void;
}
