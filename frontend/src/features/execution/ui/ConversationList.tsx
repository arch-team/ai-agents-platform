// 对话历史侧边栏列表

import { memo } from 'react';

import { cn } from '@/shared/lib/cn';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatShortDateTime } from '@/shared/lib/formatDate';
import { Button, Spinner, ErrorMessage } from '@/shared/ui';

import { useConversations } from '../api/queries';
import type { Conversation } from '../api/types';

interface ConversationListProps {
  agentId?: number;
  selectedId: number | null;
  onSelect: (id: number) => void;
  onNewConversation: () => void;
}

// memo: 列表项在对话数据未变化时跳过重渲染
// onSelect 接收 id 参数而非无参闭包，避免父组件 map 中创建新函数引用导致 memo 失效
const ConversationItem = memo(function ConversationItem({
  conversation,
  isSelected,
  onSelect,
}: {
  conversation: Conversation;
  isSelected: boolean;
  onSelect: (id: number) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(conversation.id)}
      aria-current={isSelected ? 'true' : undefined}
      className={cn(
        'w-full rounded-lg px-3 py-2 text-left transition-colors',
        'hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
        isSelected && 'bg-blue-50 ring-1 ring-blue-200',
      )}
    >
      <div className="truncate text-sm font-medium text-gray-900">
        {conversation.title || `对话 #${conversation.id}`}
      </div>
      <div className="mt-0.5 flex items-center justify-between text-xs text-gray-500">
        <span>{conversation.message_count} 条消息</span>
        <time dateTime={conversation.updated_at}>
          {formatShortDateTime(conversation.updated_at)}
        </time>
      </div>
    </button>
  );
});

export function ConversationList({
  agentId,
  selectedId,
  onSelect,
  onNewConversation,
}: ConversationListProps) {
  const { data, isLoading, error } = useConversations(agentId);

  return (
    <aside
      className="flex h-full w-64 flex-col border-r border-gray-200 bg-white"
      aria-label="对话列表"
    >
      <div className="border-b border-gray-200 p-3">
        <Button onClick={onNewConversation} variant="primary" size="sm" className="w-full">
          新建对话
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {isLoading && (
          <div className="flex justify-center py-8">
            <Spinner size="sm" />
          </div>
        )}

        {error && (
          <ErrorMessage error={extractApiError(error, '加载对话列表失败')} className="m-2" />
        )}

        {data && data.items.length === 0 && (
          <p className="px-3 py-8 text-center text-sm text-gray-400">暂无对话</p>
        )}

        {data && (
          <nav aria-label="对话历史" className="flex flex-col gap-1">
            {data.items.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isSelected={selectedId === conversation.id}
                onSelect={onSelect}
              />
            ))}
          </nav>
        )}
      </div>
    </aside>
  );
}
