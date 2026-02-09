// 流式打字指示器 — 三个跳动的点动画

import { cn } from '@/shared/lib/cn';

interface StreamingIndicatorProps {
  className?: string;
}

export function StreamingIndicator({ className }: StreamingIndicatorProps) {
  return (
    <div
      className={cn('flex items-center gap-1 text-sm text-gray-500', className)}
      role="status"
      aria-label="AI 正在输入"
    >
      <span className="text-gray-500">AI 正在输入</span>
      <span className="flex gap-0.5">
        <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
        <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
        <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
      </span>
    </div>
  );
}
