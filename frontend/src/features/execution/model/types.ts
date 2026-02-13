// Chat Store 类型定义

export interface ChatState {
  currentConversationId: number | null;
  streamingContent: string;
  isStreaming: boolean;
  error: string | null;
  setCurrentConversation: (id: number | null) => void;
  appendStreamContent: (conversationId: number, content: string) => void;
  clearStream: () => void;
  setStreaming: (streaming: boolean) => void;
  setError: (error: string) => void;
  clearError: () => void;
}
