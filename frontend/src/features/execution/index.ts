// UI 组件
export { ChatInterface } from './ui/ChatInterface';
export { MessageBubble, StreamingBubble } from './ui/MessageBubble';
export { MessageInput } from './ui/MessageInput';
export { ConversationList } from './ui/ConversationList';
export { StreamingIndicator } from './ui/StreamingIndicator';

// Hooks
export {
  useConversations,
  useConversation,
  useCreateConversation,
  useCompleteConversation,
} from './api/queries';
export { useSendMessageStream } from './api/stream';
export {
  useChatStore,
  useStreamingContent,
  useIsStreaming,
  useCurrentConversationId,
  useChatActions,
} from './model/store';

// 类型
export type {
  Conversation,
  Message,
  ConversationDetail,
  SSEChunk,
  CreateConversationDTO,
  SendMessageDTO,
} from './api/types';
export type { ChatState } from './model/types';
