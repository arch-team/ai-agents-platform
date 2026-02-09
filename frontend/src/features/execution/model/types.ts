// Chat Store 类型定义

export interface ChatState {
  currentConversationId: number | null;
  streamingContent: string;
  isStreaming: boolean;
  setCurrentConversation: (id: number | null) => void;
  appendStreamContent: (content: string) => void;
  clearStream: () => void;
  setStreaming: (streaming: boolean) => void;
}
