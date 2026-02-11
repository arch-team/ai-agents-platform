// 核心对话界面组件

import { useCallback, useEffect, useRef } from 'react';

import { ErrorMessage, Spinner } from '@/shared/ui';

import { useConversation } from '../api/queries';
import { useSendMessageStream } from '../api/stream';
import { useIsStreaming, useStreamingContent, useChatError, useChatActions } from '../model/store';

import { MessageBubble, StreamingBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { StreamingIndicator } from './StreamingIndicator';

interface ChatInterfaceProps {
  conversationId: number;
  /** 认证 token，由调用方从 auth store 获取后传入（避免跨 feature 依赖） */
  token: string | null;
}

export function ChatInterface({ conversationId, token }: ChatInterfaceProps) {
  const { data, isLoading, error } = useConversation(conversationId);
  const { sendMessage } = useSendMessageStream(token);
  const streamingContent = useStreamingContent();
  const isStreaming = useIsStreaming();
  const chatError = useChatError();
  const { clearStream, clearError } = useChatActions();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 切换对话时清理流式状态
  useEffect(() => {
    clearStream();
  }, [conversationId, clearStream]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [data?.messages, streamingContent]);

  const handleSend = useCallback(
    (content: string) => {
      clearError();
      sendMessage(conversationId, { content });
    },
    [conversationId, sendMessage, clearError],
  );

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <ErrorMessage error="加载对话失败，请重试" />
      </div>
    );
  }

  const messages = data?.messages ?? [];
  const isCompleted = data?.conversation.status === 'completed';

  return (
    <div className="flex h-full flex-col">
      {/* 对话标题栏 */}
      <header className="border-b border-gray-200 bg-white px-4 py-3">
        <h2 className="text-lg font-semibold text-gray-900">
          {data?.conversation.title || `对话 #${conversationId}`}
        </h2>
        {isCompleted && <span className="text-xs text-gray-500">对话已结束</span>}
      </header>

      {/* 消息列表 */}
      <div
        className="flex-1 overflow-y-auto p-4"
        role="log"
        aria-label="消息列表"
        aria-live="polite"
      >
        {messages.length === 0 && !isStreaming && (
          <p className="py-12 text-center text-sm text-gray-400">开始新的对话吧</p>
        )}

        <div className="flex flex-col gap-3">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* 流式消息展示 */}
          {streamingContent && <StreamingBubble content={streamingContent} />}

          {/* 流式输入指示器 */}
          {isStreaming && !streamingContent && <StreamingIndicator />}
        </div>

        <div ref={messagesEndRef} />
      </div>

      {/* 流式错误提示 */}
      {chatError && (
        <div className="border-t border-red-100 bg-red-50 px-4 py-2">
          <ErrorMessage error={chatError} className="border-0 bg-transparent p-0" />
        </div>
      )}

      {/* 消息输入框 */}
      {!isCompleted && <MessageInput onSend={handleSend} disabled={isStreaming} />}
    </div>
  );
}
