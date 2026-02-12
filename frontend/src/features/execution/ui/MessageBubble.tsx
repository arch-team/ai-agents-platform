// 消息气泡组件 — 用户/AI 不同样式

import { memo } from 'react';

import { cn } from '@/shared/lib/cn';
import { formatTime } from '@/shared/lib/formatDate';

import type { Message } from '../api/types';

interface MessageBubbleProps {
  message: Message;
}

// memo: 消息列表中的每条消息在渲染后 props 不再变化，避免父组件更新时无意义重渲染
export const MessageBubble = memo(function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  // 隐藏空内容的助手消息（SDK 调用失败时后端可能创建空 assistant 消息）
  if (!isUser && !message.content.trim()) {
    return null;
  }

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[75%] rounded-lg px-4 py-2',
          isUser ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900',
        )}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        <time
          className={cn('mt-1 block text-xs', isUser ? 'text-blue-200' : 'text-gray-400')}
          dateTime={message.created_at}
        >
          {formatTime(message.created_at)}
        </time>
      </div>
    </div>
  );
});

// 流式消息气泡 — 显示累积中的 AI 响应
// 调用方已确保 content 非空才渲染，此处无需重复检查
interface StreamingBubbleProps {
  content: string;
}

export function StreamingBubble({ content }: StreamingBubbleProps) {
  return (
    <div className="flex w-full justify-start">
      <div className="max-w-[75%] rounded-lg bg-gray-100 px-4 py-2 text-gray-900">
        <p className="whitespace-pre-wrap break-words">{content}</p>
      </div>
    </div>
  );
}
