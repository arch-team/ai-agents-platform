// 模板卡片网格列表组件
import { useState } from 'react';

import { Button, Card, Spinner, ErrorMessage, Pagination } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';

import { useTemplates, useDeleteTemplate, usePublishTemplate, useArchiveTemplate } from '../api/queries';
import type { TemplateFilters, TemplateCategory, TemplateStatus } from '../api/types';

import { TemplateStatusBadge } from './TemplateStatusBadge';
import { CategoryFilter, CATEGORY_CONFIG } from './CategoryFilter';

const STATUS_OPTIONS: Array<{ value: TemplateStatus | ''; label: string }> = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '已发布' },
  { value: 'archived', label: '已归档' },
];

interface TemplateListProps {
  onSelect?: (id: number) => void;
  onCreate?: () => void;
}

export function TemplateList({ onSelect, onCreate }: TemplateListProps) {
  const [filters, setFilters] = useState<TemplateFilters>({ page: 1, page_size: 12 });
  const [operatingId, setOperatingId] = useState<number | null>(null);
  const { data, isLoading, error } = useTemplates(filters);

  const deleteMutation = useDeleteTemplate();
  const publishMutation = usePublishTemplate();
  const archiveMutation = useArchiveTemplate();

  const handleDelete = (id: number) => {
    setOperatingId(id);
    deleteMutation.mutate(id, { onSettled: () => setOperatingId(null) });
  };

  const handlePublish = (id: number) => {
    setOperatingId(id);
    publishMutation.mutate(id, { onSettled: () => setOperatingId(null) });
  };

  const handleArchive = (id: number) => {
    setOperatingId(id);
    archiveMutation.mutate(id, { onSettled: () => setOperatingId(null) });
  };

  const handleCategoryChange = (category: TemplateCategory | undefined) => {
    setFilters((prev) => ({ ...prev, category, page: 1 }));
  };

  const handleStatusFilter = (status: TemplateStatus | '') => {
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
    return <ErrorMessage error={extractApiError(error, '加载模板列表失败')} />;
  }

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label htmlFor="template-status-filter" className="text-sm font-medium text-gray-700">
              状态
            </label>
            <select
              id="template-status-filter"
              value={filters.status ?? ''}
              onChange={(e) => handleStatusFilter(e.target.value as TemplateStatus | '')}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        {onCreate && (
          <Button onClick={onCreate} size="sm">
            创建模板
          </Button>
        )}
      </div>

      {/* 分类筛选 */}
      <CategoryFilter selected={filters.category} onChange={handleCategoryChange} />

      {/* 模板卡片网格 */}
      {!data?.items.length ? (
        <div className="py-12 text-center text-gray-500" role="status">
          暂无模板
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((template) => (
            <Card key={template.id} className="flex flex-col transition-shadow hover:shadow-md">
              <button
                type="button"
                className="flex-1 text-left"
                onClick={() => onSelect?.(template.id)}
                aria-label={`查看模板: ${template.name}`}
              >
                <div className="mb-2 flex items-center gap-2">
                  <TemplateStatusBadge status={template.status} />
                  <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                    {CATEGORY_CONFIG[template.category]?.label ?? template.category}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-gray-900">{template.name}</h3>
                {template.description && (
                  <p className="mt-1 line-clamp-2 text-sm text-gray-600">{template.description}</p>
                )}
                <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
                  <span>使用 {template.use_count} 次</span>
                  <span>{formatDateTime(template.updated_at)}</span>
                </div>
              </button>
              <div className="mt-4 flex gap-2 border-t border-gray-100 pt-3">
                {template.status === 'draft' && (
                  <Button
                    variant="primary"
                    size="sm"
                    loading={publishMutation.isPending && operatingId === template.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePublish(template.id);
                    }}
                    aria-label={`发布 ${template.name}`}
                  >
                    发布
                  </Button>
                )}
                {template.status === 'published' && (
                  <Button
                    variant="outline"
                    size="sm"
                    loading={archiveMutation.isPending && operatingId === template.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleArchive(template.id);
                    }}
                    aria-label={`归档 ${template.name}`}
                  >
                    归档
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  loading={deleteMutation.isPending && operatingId === template.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(template.id);
                  }}
                  aria-label={`删除 ${template.name}`}
                >
                  删除
                </Button>
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
