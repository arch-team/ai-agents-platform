// 消息输入框 + 发送按钮

import { useCallback, useRef, useState } from 'react';

import { cn } from '@/shared/lib/cn';
import { Button } from '@/shared/ui';

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  className?: string;
}

export function MessageInput({ onSend, disabled = false, className }: MessageInputProps) {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSend = content.trim().length > 0 && !disabled;

  const handleSend = useCallback(() => {
    const trimmed = content.trim();
    if (!trimmed || disabled) return;

    onSend(trimmed);
    setContent('');

    // 重置 textarea 高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [content, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Enter 发送，Shift+Enter 换行
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    // 自动调整高度
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  };

  return (
    <div className={cn('flex items-end gap-2 border-t border-gray-200 bg-white p-4', className)}>
      <textarea
        ref={textareaRef}
        value={content}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? 'AI 正在回复中...' : '输入消息，Enter 发送，Shift+Enter 换行'}
        rows={1}
        aria-label="消息输入"
        className={cn(
          'flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm',
          'focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500',
          'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-400',
        )}
      />
      <Button onClick={handleSend} disabled={!canSend} size="md" aria-label="发送消息">
        发送
      </Button>
    </div>
  );
}
