// 记忆管理面板 — 展示、搜索和删除 Agent 记忆

import { useState } from 'react';

import { Button, Card, Spinner, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useAgentMemories, useSearchMemories, useDeleteMemory } from '../api/memory-queries';

import type { MemoryItem } from '../api/memory-queries';

interface MemoryPanelProps {
  agentId: number;
}

export function MemoryPanel({ agentId }: MemoryPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MemoryItem[] | null>(null);

  const { data: memories, isLoading, error } = useAgentMemories(agentId);
  const searchMutation = useSearchMemories(agentId);
  const deleteMutation = useDeleteMemory(agentId);

  // 搜索记忆
  const handleSearch = () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    searchMutation.mutate(
      { query: searchQuery.trim(), max_results: 20 },
      { onSuccess: (data) => setSearchResults(data) },
    );
  };

  // 清除搜索结果，回到列表视图
  const handleClearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  // 删除记忆
  const handleDelete = (memoryId: string) => {
    deleteMutation.mutate(memoryId, {
      onSuccess: () => {
        // 同时从搜索结果中移除
        if (searchResults) {
          setSearchResults(searchResults.filter((m) => m.memory_id !== memoryId));
        }
      },
    });
  };

  // 当前展示的记忆列表：搜索结果优先
  const displayItems = searchResults ?? memories ?? [];

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">记忆管理</h2>
      </div>

      {/* 搜索栏 */}
      <div className="mb-4 flex gap-2">
        <input
          type="search"
          aria-label="搜索记忆"
          placeholder="输入关键词搜索记忆..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        />
        <Button size="sm" onClick={handleSearch} loading={searchMutation.isPending}>
          搜索
        </Button>
        {searchResults && (
          <Button size="sm" variant="outline" onClick={handleClearSearch}>
            清除
          </Button>
        )}
      </div>

      {/* 错误提示 */}
      {error && <ErrorMessage error={extractApiError(error, '加载记忆列表失败')} />}
      {searchMutation.isError && (
        <ErrorMessage error={extractApiError(searchMutation.error, '搜索记忆失败')} />
      )}
      {deleteMutation.isError && (
        <ErrorMessage error={extractApiError(deleteMutation.error, '删除记忆失败')} />
      )}

      {/* 加载状态 */}
      {isLoading && (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      )}

      {/* 空状态 */}
      {!isLoading && !error && displayItems.length === 0 && (
        <p className="py-8 text-center text-sm text-gray-500">
          {searchResults !== null
            ? '未找到匹配的记忆'
            : '该 Agent 暂无记忆。对话时会自动提取和保存记忆。'}
        </p>
      )}

      {/* 记忆列表 */}
      {displayItems.length > 0 && (
        <ul className="divide-y divide-gray-100" role="list" aria-label="记忆列表">
          {displayItems.map((item) => (
            <li key={item.memory_id} className="flex items-start gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm text-gray-900">{item.content}</p>
                <div className="mt-1 flex items-center gap-2">
                  {item.topic && (
                    <span className="inline-flex rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                      {item.topic}
                    </span>
                  )}
                  {searchResults !== null && item.relevance_score > 0 && (
                    <span className="text-xs text-gray-400">
                      相关度: {(item.relevance_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <span className="text-xs text-gray-400" title={item.memory_id}>
                    {item.memory_id.slice(0, 8)}...
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(item.memory_id)}
                disabled={deleteMutation.isPending}
                aria-label={`删除记忆 ${item.memory_id.slice(0, 8)}`}
                className="shrink-0 rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50 hover:text-red-700 disabled:opacity-50"
              >
                删除
              </button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
