// 流式内容展示区 — 独立组件，避免流式更新触发历史消息重渲染

import { memo } from 'react';

import { StreamingBubble } from './MessageBubble';
import { StreamingIndicator } from './StreamingIndicator';

interface StreamingAreaProps {
  streamingContent: string;
  isStreaming: boolean;
}

// memo: streamingContent 每次 SSE chunk 都会更新，
// 将其隔离在独立组件中，避免历史消息列表随之重渲染
export const StreamingArea = memo(function StreamingArea({
  streamingContent,
  isStreaming,
}: StreamingAreaProps) {
  return (
    <>
      {/* 流式消息展示 */}
      {streamingContent && <StreamingBubble content={streamingContent} />}

      {/* 流式输入指示器 */}
      {isStreaming && !streamingContent && <StreamingIndicator />}
    </>
  );
});
