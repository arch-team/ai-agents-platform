// 对话相关类型定义

export interface Conversation {
  id: number;
  title: string;
  agent_id: number;
  user_id: number;
  status: 'active' | 'completed' | 'failed';
  message_count: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  token_count: number;
  created_at: string;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: Message[];
}

export interface SSEChunk {
  content: string;
  done: boolean;
  message_id?: number;
  token_count?: number;
  error?: string;
}

export interface CreateConversationDTO {
  agent_id: number;
  title?: string;
}

export interface SendMessageDTO {
  content: string;
}
