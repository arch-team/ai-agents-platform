// 测试集列表组件

import { useState } from 'react';

import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';
import { Button, Spinner, ErrorMessage, Pagination } from '@/shared/ui';

import { useTestSuites, useActivateTestSuite, useArchiveTestSuite, useDeleteTestSuite } from '../api/queries';

import type { TestSuiteStatus, TestSuiteFilters } from '../api/types';

import { TestSuiteStatusBadge } from './TestSuiteStatusBadge';

const STATUS_OPTIONS: Array<{ value: TestSuiteStatus | ''; label: string }> = [
  { value: '', label: '全部' },
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '已激活' },
  { value: 'archived', label: '已归档' },
];

interface TestSuiteListProps {
  onSelect?: (id: number) => void;
  onCreate?: () => void;
}

export function TestSuiteList({ onSelect, onCreate }: TestSuiteListProps) {
  const [filters, setFilters] = useState<TestSuiteFilters>({ page: 1, page_size: 10 });
  // 前端过滤状态（后端列表接口不支持 status 参数）
  const [statusFilter, setStatusFilter] = useState<TestSuiteStatus | ''>('');
  const [operatingId, setOperatingId] = useState<number | null>(null);
  const { data, isLoading, error } = useTestSuites(filters);

  const mutationCallbacks = { onSettled: () => setOperatingId(null) };
  const activateMutation = useActivateTestSuite();
  const archiveMutation = useArchiveTestSuite();
  const deleteMutation = useDeleteTestSuite();

  const handleActivate = (id: number) => {
    setOperatingId(id);
    activateMutation.mutate(id, mutationCallbacks);
  };

  const handleArchive = (id: number) => {
    setOperatingId(id);
    archiveMutation.mutate(id, mutationCallbacks);
  };

  const handleDelete = (id: number) => {
    setOperatingId(id);
    deleteMutation.mutate(id, mutationCallbacks);
  };

  const handleStatusFilter = (status: TestSuiteStatus | '') => {
    setStatusFilter(status);
    setFilters((prev) => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const filteredItems = statusFilter
    ? data?.items.filter((s) => s.status === statusFilter)
    : data?.items;

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error={extractApiError(error, '加载测试集列表失败')} />;
  }

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label htmlFor="suite-status-filter" className="text-sm font-medium text-gray-700">
            状态筛选
          </label>
          <select
            id="suite-status-filter"
            value={statusFilter}
            onChange={(e) => handleStatusFilter(e.target.value as TestSuiteStatus | '')}
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
            创建测试集
          </Button>
        )}
      </div>

      {/* 列表 */}
      {!filteredItems?.length ? (
        <div className="py-12 text-center text-gray-500" role="status">
          暂无测试集
        </div>
      ) : (
        <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">
          {filteredItems.map((suite) => (
            <div key={suite.id} className="flex items-center justify-between p-4 hover:bg-gray-50">
              <button
                type="button"
                className="flex-1 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                onClick={() => onSelect?.(suite.id)}
                aria-label={`查看测试集: ${suite.name}`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-900">{suite.name}</span>
                  <TestSuiteStatusBadge status={suite.status} />
                </div>
                {suite.description && (
                  <p className="mt-1 text-sm text-gray-500">{suite.description}</p>
                )}
                <p className="mt-1 text-xs text-gray-400">
                  创建于 {formatDateTime(suite.created_at)}
                </p>
              </button>
              <div className="ml-4 flex shrink-0 gap-2">
                {suite.status === 'draft' && (
                  <Button
                    variant="primary"
                    size="sm"
                    loading={activateMutation.isPending && operatingId === suite.id}
                    onClick={() => handleActivate(suite.id)}
                    aria-label={`激活 ${suite.name}`}
                  >
                    激活
                  </Button>
                )}
                {suite.status === 'active' && (
                  <Button
                    variant="outline"
                    size="sm"
                    loading={archiveMutation.isPending && operatingId === suite.id}
                    onClick={() => handleArchive(suite.id)}
                    aria-label={`归档 ${suite.name}`}
                  >
                    归档
                  </Button>
                )}
                {suite.status === 'draft' && (
                  <Button
                    variant="outline"
                    size="sm"
                    loading={deleteMutation.isPending && operatingId === suite.id}
                    onClick={() => handleDelete(suite.id)}
                    aria-label={`删除 ${suite.name}`}
                  >
                    删除
                  </Button>
                )}
              </div>
            </div>
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
