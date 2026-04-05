// Builder Zustand store 类型定义

import type {
  BlueprintConfigOverrides,
  BuilderPhase,
  ChatMessage,
  GeneratedBlueprint,
} from '../api/types';

export interface BuilderState {
  // ── 共享状态 ──
  sessionId: number | null;
  streamContent: string;
  isGenerating: boolean;
  isConfirming: boolean;
  error: string | null;

  // ── Blueprint 状态 ──
  phase: BuilderPhase;
  messages: ChatMessage[];
  generatedBlueprint: GeneratedBlueprint | null;
  configOverrides: BlueprintConfigOverrides;
  createdAgentId: number | null;

  // ── 共享 Actions ──
  setSessionId: (id: number | null) => void;
  appendStreamContent: (content: string) => void;
  setGenerating: (generating: boolean) => void;
  setConfirming: (confirming: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;

  // ── Blueprint Actions ──
  setPhase: (phase: BuilderPhase) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setGeneratedBlueprint: (blueprint: GeneratedBlueprint | null) => void;
  setCreatedAgentId: (id: number | null) => void;
  setConfigOverrides: (overrides: Partial<BlueprintConfigOverrides>) => void;
  resetStream: () => void;
}
