// Zustand store: 当前对话状态 + 流式消息缓冲

import { create } from 'zustand';
import { useShallow } from 'zustand/shallow';

import type { ChatState } from './types';

export const useChatStore = create<ChatState>()((set) => ({
  currentConversationId: null,
  streamingContent: '',
  isStreaming: false,
  error: null,
  setCurrentConversation: (id) => set({ currentConversationId: id }),
  appendStreamContent: (conversationId, content) =>
    set((state) => {
      // 忽略非当前对话的流式内容，防止多对话切换时的竞态
      if (state.currentConversationId !== null && state.currentConversationId !== conversationId) {
        return state;
      }
      return { streamingContent: state.streamingContent + content };
    }),
  clearStream: () => set({ streamingContent: '', isStreaming: false }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

// 细粒度 selector hooks
export const useStreamingContent = () => useChatStore((state) => state.streamingContent);
export const useIsStreaming = () => useChatStore((state) => state.isStreaming);
export const useCurrentConversationId = () => useChatStore((state) => state.currentConversationId);
export const useChatError = () => useChatStore((state) => state.error);
export const useChatActions = () =>
  useChatStore(
    useShallow((state) => ({
      setCurrentConversation: state.setCurrentConversation,
      appendStreamContent: state.appendStreamContent,
      clearStream: state.clearStream,
      setStreaming: state.setStreaming,
      setError: state.setError,
      clearError: state.clearError,
    })),
  );
