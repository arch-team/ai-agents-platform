// Builder Zustand store — 管理流式生成状态（服务端数据用 React Query）

import { create } from 'zustand';
import { useShallow } from 'zustand/shallow';

import type { BuilderState } from './types';

const initialState = {
  sessionId: null,
  streamContent: '',
  generatedConfig: null,
  isGenerating: false,
  isConfirming: false,
  error: null,
} as const;

export const useBuilderStore = create<BuilderState>()((set) => ({
  ...initialState,

  setSessionId: (id) => set({ sessionId: id }),

  appendStreamContent: (content) =>
    set((state) => ({ streamContent: state.streamContent + content })),

  setGeneratedConfig: (config) => set({ generatedConfig: config }),

  setGenerating: (generating) => set({ isGenerating: generating }),

  setConfirming: (confirming) => set({ isConfirming: confirming }),

  setError: (error) => set({ error }),

  reset: () => set({ ...initialState }),
}));

// 细粒度 selector hooks，避免不必要的重渲染
export const useBuilderSessionId = () => useBuilderStore((state) => state.sessionId);
export const useBuilderStreamContent = () => useBuilderStore((state) => state.streamContent);
export const useBuilderGeneratedConfig = () => useBuilderStore((state) => state.generatedConfig);
export const useBuilderIsGenerating = () => useBuilderStore((state) => state.isGenerating);
export const useBuilderIsConfirming = () => useBuilderStore((state) => state.isConfirming);
export const useBuilderError = () => useBuilderStore((state) => state.error);

export const useBuilderActions = () =>
  useBuilderStore(
    useShallow((state) => ({
      setSessionId: state.setSessionId,
      appendStreamContent: state.appendStreamContent,
      setGeneratedConfig: state.setGeneratedConfig,
      setGenerating: state.setGenerating,
      setConfirming: state.setConfirming,
      setError: state.setError,
      reset: state.reset,
    })),
  );
