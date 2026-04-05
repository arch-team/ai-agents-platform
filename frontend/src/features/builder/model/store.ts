// Builder Zustand store — 管理流式生成状态 + V2 阶段/蓝图状态

import { create } from 'zustand';
import { useShallow } from 'zustand/shallow';

import type { BuilderState } from './types';

const initialState: Pick<
  BuilderState,
  | 'sessionId'
  | 'streamContent'
  | 'isGenerating'
  | 'isConfirming'
  | 'error'
  | 'phase'
  | 'messages'
  | 'generatedBlueprint'
  | 'configOverrides'
  | 'createdAgentId'
> = {
  sessionId: null,
  streamContent: '',
  isGenerating: false,
  isConfirming: false,
  error: null,
  phase: 'input',
  messages: [],
  generatedBlueprint: null,
  configOverrides: {},
  createdAgentId: null,
};

export const useBuilderStore = create<BuilderState>()((set) => ({
  ...initialState,

  // 共享 actions
  setSessionId: (id) => set({ sessionId: id }),
  appendStreamContent: (content) =>
    set((state) => ({ streamContent: state.streamContent + content })),
  setGenerating: (generating) => set({ isGenerating: generating }),
  setConfirming: (confirming) => set({ isConfirming: confirming }),
  setError: (error) => set({ error }),
  reset: () => set({ ...initialState }),

  // Blueprint actions
  setPhase: (phase) => set({ phase }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  setGeneratedBlueprint: (blueprint) => set({ generatedBlueprint: blueprint }),
  setCreatedAgentId: (id) => set({ createdAgentId: id }),
  setConfigOverrides: (overrides) =>
    set((state) => ({ configOverrides: { ...state.configOverrides, ...overrides } })),
  resetStream: () => set({ streamContent: '', error: null }),
}));

// ── 细粒度 selector hooks ──

// 共享 selectors
export const useBuilderSessionId = () => useBuilderStore((s) => s.sessionId);
export const useBuilderStreamContent = () => useBuilderStore((s) => s.streamContent);
export const useBuilderIsGenerating = () => useBuilderStore((s) => s.isGenerating);
export const useBuilderIsConfirming = () => useBuilderStore((s) => s.isConfirming);
export const useBuilderError = () => useBuilderStore((s) => s.error);

// Blueprint selectors
export const useBuilderPhase = () => useBuilderStore((s) => s.phase);
export const useBuilderMessages = () => useBuilderStore((s) => s.messages);
export const useBuilderBlueprint = () => useBuilderStore((s) => s.generatedBlueprint);
export const useBuilderCreatedAgentId = () => useBuilderStore((s) => s.createdAgentId);
export const useBuilderConfigOverrides = () => useBuilderStore((s) => s.configOverrides);

// Actions bundle
export const useBuilderActions = () =>
  useBuilderStore(
    useShallow((s) => ({
      setSessionId: s.setSessionId,
      appendStreamContent: s.appendStreamContent,
      setGenerating: s.setGenerating,
      setConfirming: s.setConfirming,
      setError: s.setError,
      reset: s.reset,
      setPhase: s.setPhase,
      addMessage: s.addMessage,
      setMessages: s.setMessages,
      setGeneratedBlueprint: s.setGeneratedBlueprint,
      setCreatedAgentId: s.setCreatedAgentId,
      setConfigOverrides: s.setConfigOverrides,
      resetStream: s.resetStream,
    })),
  );
