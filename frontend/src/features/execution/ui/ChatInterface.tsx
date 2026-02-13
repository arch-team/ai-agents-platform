// 核心对话界面组件

import { memo, useCallback, useEffect, useRef } from 'react';

import { ErrorMessage, Spinner } from '@/shared/ui';

import { useConversation } from '../api/queries';
import { useSendMessageStream } from '../api/stream';
import type { Message } from '../api/types';
import { useIsStreaming, useStreamingContent, useChatError, useChatActions } from '../model/store';

import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { StreamingArea } from './StreamingArea';

interface ChatInterfaceProps {
  conversationId: number;
  /** 认证 token，由调用方从 auth store 获取后传入（避免跨 feature 依赖） */
  token: string | null;
}

// 历史消息列表 — 独立 memo 组件，仅在 messages 数组变化时重渲染
interface MessageListProps {
  messages: Message[];
}

const MessageList = memo(function MessageList({ messages }: MessageListProps) {
  return (
    <>
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
    </>
  );
});

export function ChatInterface({ conversationId, token }: ChatInterfaceProps) {
  const { data, isLoading, error } = useConversation(conversationId);
  const { sendMessage } = useSendMessageStream(token);
  const streamingContent = useStreamingContent();
  const isStreaming = useIsStreaming();
  const chatError = useChatError();
  const { clearStream, clearError } = useChatActions();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // aria-live 通知区域 DOM ref + 上次消息数量追踪
  const liveRegionRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef(0);

  // 新消息到达时更新无障碍通知
  // 通过直接操作 DOM textContent，避免 setState-in-effect lint 报错
  useEffect(() => {
    const currentCount = data?.messages?.length ?? 0;
    if (currentCount > prevMessageCountRef.current && currentCount > 0) {
      const lastMessage = data!.messages[currentCount - 1];
      if (liveRegionRef.current) {
        liveRegionRef.current.textContent = `收到新消息: ${lastMessage.content}`;
      }
    } else if (currentCount === 0 && liveRegionRef.current) {
      liveRegionRef.current.textContent = '';
    }
    prevMessageCountRef.current = currentCount;
  }, [data]);

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

      {/* 消息列表 — 不使用 aria-live，避免流式更新时屏幕阅读器不断朗读 */}
      <div className="flex-1 overflow-y-auto p-4" role="log" aria-label="消息列表">
        {messages.length === 0 && !isStreaming && (
          <p className="py-12 text-center text-sm text-gray-400">开始新的对话吧</p>
        )}

        <div className="flex flex-col gap-3">
          {/* 历史消息 — 独立 memo 组件，不受 streamingContent 更新影响 */}
          <MessageList messages={messages} />

          {/* 流式展示区 — 独立 memo 组件，仅 streamingContent/isStreaming 变化时更新 */}
          <StreamingArea streamingContent={streamingContent} isStreaming={isStreaming} />
        </div>

        <div ref={messagesEndRef} />
      </div>

      {/* 新消息通知 — 通过 effect + DOM ref 更新，仅在新消息到达时触发朗读 */}
      <div ref={liveRegionRef} aria-live="polite" aria-atomic="true" className="sr-only" />

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
