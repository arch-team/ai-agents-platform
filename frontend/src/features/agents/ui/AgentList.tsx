import { useState } from 'react';

import { AgentCard } from '@/entities/agent';
import type { AgentStatus } from '@/entities/agent';
import { Button, Spinner, ErrorMessage } from '@/shared/ui';

import { useAgents, useActivateAgent, useArchiveAgent, useDeleteAgent } from '../api/queries';
import type { AgentFilters } from '../model/types';

const STATUS_OPTIONS: Array<{ value: AgentStatus | ''; label: string }> = [
  { value: '', label: '全部' },
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '已激活' },
  { value: 'archived', label: '已归档' },
];

interface AgentListProps {
  onSelect?: (id: number) => void;
  onEdit?: (id: number) => void;
  onCreate?: () => void;
}

export function AgentList({ onSelect, onEdit, onCreate }: AgentListProps) {
  const [filters, setFilters] = useState<AgentFilters>({ page: 1, page_size: 10 });
  const { data, isLoading, error } = useAgents(filters);
  const activateMutation = useActivateAgent();
  const archiveMutation = useArchiveAgent();
  const deleteMutation = useDeleteAgent();

  const handleStatusFilter = (status: AgentStatus | '') => {
    setFilters((prev) => ({
      ...prev,
      status: status || undefined,
      page: 1,
    }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error={error instanceof Error ? error.message : '加载失败'} />;
  }

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
            状态筛选
          </label>
          <select
            id="status-filter"
            value={filters.status ?? ''}
            onChange={(e) => handleStatusFilter(e.target.value as AgentStatus | '')}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        {onCreate && (
          <Button onClick={onCreate} size="sm">
            创建 Agent
          </Button>
        )}
      </div>

      {/* 列表 */}
      {!data?.items.length ? (
        <div className="py-12 text-center text-gray-500" role="status">
          暂无 Agent
        </div>
      ) : (
        <div className="grid gap-4">
          {data.items.map((agent) => (
            <div key={agent.id} className="flex items-start gap-3">
              <div className="min-w-0 flex-1">
                <AgentCard agent={agent} onClick={() => onSelect?.(agent.id)} />
              </div>
              <div className="flex shrink-0 flex-col gap-2 pt-6">
                {agent.status === 'draft' && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onEdit?.(agent.id)}
                      aria-label={`编辑 ${agent.name}`}
                    >
                      编辑
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      loading={activateMutation.isPending}
                      onClick={() => activateMutation.mutate(agent.id)}
                      aria-label={`激活 ${agent.name}`}
                    >
                      激活
                    </Button>
                  </>
                )}
                {agent.status === 'active' && (
                  <Button
                    variant="outline"
                    size="sm"
                    loading={archiveMutation.isPending}
                    onClick={() => archiveMutation.mutate(agent.id)}
                    aria-label={`归档 ${agent.name}`}
                  >
                    归档
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  loading={deleteMutation.isPending}
                  onClick={() => deleteMutation.mutate(agent.id)}
                  aria-label={`删除 ${agent.name}`}
                >
                  删除
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {data && data.total_pages > 1 && (
        <nav aria-label="分页导航" className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={data.page <= 1}
            onClick={() => handlePageChange(data.page - 1)}
          >
            上一页
          </Button>
          <span className="text-sm text-gray-600">
            第 {data.page} / {data.total_pages} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={data.page >= data.total_pages}
            onClick={() => handlePageChange(data.page + 1)}
          >
            下一页
          </Button>
        </nav>
      )}
    </div>
  );
}
