// 知识库列表组件
import { useState } from 'react';

import { Button, Card, Spinner, ErrorMessage, Pagination } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';

import { useKnowledgeBases, useDeleteKnowledgeBase, useSyncKnowledgeBase } from '../api/queries';
import type { KnowledgeBaseFilters, KnowledgeBaseStatus } from '../api/types';

import { KnowledgeStatusBadge } from './KnowledgeStatusBadge';

const STATUS_OPTIONS: Array<{ value: KnowledgeBaseStatus | ''; label: string }> = [
  { value: '', label: '全部' },
  { value: 'CREATING', label: '创建中' },
  { value: 'ACTIVE', label: '已激活' },
  { value: 'SYNCING', label: '同步中' },
  { value: 'FAILED', label: '失败' },
];

interface KnowledgeListProps {
  onSelect?: (id: number) => void;
  onCreate?: () => void;
}

export function KnowledgeList({ onSelect, onCreate }: KnowledgeListProps) {
  const [filters, setFilters] = useState<KnowledgeBaseFilters>({ page: 1, page_size: 10 });
  const [operatingId, setOperatingId] = useState<number | null>(null);
  const { data, isLoading, error } = useKnowledgeBases(filters);

  const deleteMutation = useDeleteKnowledgeBase();
  const syncMutation = useSyncKnowledgeBase();

  const handleDelete = (id: number) => {
    setOperatingId(id);
    deleteMutation.mutate(id, { onSettled: () => setOperatingId(null) });
  };

  const handleSync = (id: number) => {
    setOperatingId(id);
    syncMutation.mutate(id, { onSettled: () => setOperatingId(null) });
  };

  const handleStatusFilter = (status: KnowledgeBaseStatus | '') => {
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
    return <ErrorMessage error={extractApiError(error, '加载知识库列表失败')} />;
  }

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label htmlFor="kb-status-filter" className="text-sm font-medium text-gray-700">
            状态筛选
          </label>
          <select
            id="kb-status-filter"
            value={filters.status ?? ''}
            onChange={(e) => handleStatusFilter(e.target.value as KnowledgeBaseStatus | '')}
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
            创建知识库
          </Button>
        )}
      </div>

      {/* 列表 */}
      {!data?.items.length ? (
        <div className="py-12 text-center text-gray-500" role="status">
          暂无知识库
        </div>
      ) : (
        <div className="grid gap-4">
          {data.items.map((kb) => (
            <Card key={kb.id} className="cursor-pointer transition-shadow hover:shadow-md">
              <div className="flex items-start justify-between">
                <button
                  type="button"
                  className="min-w-0 flex-1 text-left"
                  onClick={() => onSelect?.(kb.id)}
                  aria-label={`查看知识库: ${kb.name}`}
                >
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-gray-900">{kb.name}</h3>
                    <KnowledgeStatusBadge status={kb.status} />
                  </div>
                  {kb.description && (
                    <p className="mt-1 text-sm text-gray-600">{kb.description}</p>
                  )}
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span>{kb.document_count} 个文档</span>
                    <span>创建于 {formatDateTime(kb.created_at)}</span>
                  </div>
                </button>
                <div className="ml-4 flex shrink-0 gap-2">
                  {kb.status === 'ACTIVE' && (
                    <Button
                      variant="outline"
                      size="sm"
                      loading={syncMutation.isPending && operatingId === kb.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSync(kb.id);
                      }}
                      aria-label={`同步 ${kb.name}`}
                    >
                      同步
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    loading={deleteMutation.isPending && operatingId === kb.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(kb.id);
                    }}
                    aria-label={`删除 ${kb.name}`}
                  >
                    删除
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 分页 */}
      {data && (
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
