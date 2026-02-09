// 消息气泡组件 — 用户/AI 不同样式

import { cn } from '@/shared/lib/cn';

import type { Message } from '../api/types';

interface MessageBubbleProps {
  message: Message;
}

function formatTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

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
}

// 流式消息气泡 — 显示累积中的 AI 响应
interface StreamingBubbleProps {
  content: string;
}

export function StreamingBubble({ content }: StreamingBubbleProps) {
  if (!content) return null;

  return (
    <div className="flex w-full justify-start">
      <div className="max-w-[75%] rounded-lg bg-gray-100 px-4 py-2 text-gray-900">
        <p className="whitespace-pre-wrap break-words">{content}</p>
      </div>
    </div>
  );
}
