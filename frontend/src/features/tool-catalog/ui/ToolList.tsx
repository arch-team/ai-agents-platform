// 工具列表组件

import { useState } from 'react';

import { Button, Card, Spinner, ErrorMessage, Pagination } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';

import { useTools } from '../api/queries';
import type { ToolStatus, ToolType, ToolFilters, Tool } from '../api/types';
import { TOOL_TYPE_LABELS } from '../api/types';

import { ToolStatusBadge } from './ToolStatusBadge';
import { ToolRegisterDialog } from './ToolRegisterDialog';

// 状态筛选选项
const STATUS_OPTIONS: Array<{ value: ToolStatus | ''; label: string }> = [
  { value: '', label: '全部状态' },
  { value: 'DRAFT', label: '草稿' },
  { value: 'PENDING_REVIEW', label: '待审批' },
  { value: 'APPROVED', label: '已审批' },
  { value: 'REJECTED', label: '已拒绝' },
  { value: 'DEPRECATED', label: '已废弃' },
];

// 工具类型筛选选项
const TYPE_OPTIONS: Array<{ value: ToolType | ''; label: string }> = [
  { value: '', label: '全部类型' },
  { value: 'MCP_SERVER', label: 'MCP Server' },
  { value: 'API', label: 'API' },
  { value: 'FUNCTION', label: 'Function' },
];

interface ToolListProps {
  onSelect?: (id: string) => void;
}

// 工具卡片子组件
function ToolCard({ tool, onSelect }: { tool: Tool; onSelect?: (id: string) => void }) {
  return (
    <Card className="cursor-pointer transition-shadow hover:shadow-md">
      <div
        role="button"
        tabIndex={0}
        onClick={() => onSelect?.(tool.id)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onSelect?.(tool.id);
          }
        }}
        aria-label={`查看工具 ${tool.name} 的详情`}
      >
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-medium text-gray-900">{tool.name}</h3>
            <p className="mt-1 line-clamp-2 text-sm text-gray-500">{tool.description}</p>
          </div>
          <ToolStatusBadge status={tool.status} className="ml-3 shrink-0" />
        </div>
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
          <span>{TOOL_TYPE_LABELS[tool.tool_type] ?? tool.tool_type}</span>
          {tool.version && <span>v{tool.version}</span>}
          <span>{formatDateTime(tool.updated_at)}</span>
        </div>
      </div>
    </Card>
  );
}

export function ToolList({ onSelect }: ToolListProps) {
  const [filters, setFilters] = useState<ToolFilters>({ page: 1, page_size: 10 });
  const [registerOpen, setRegisterOpen] = useState(false);
  const { data, isLoading, error } = useTools(filters);

  const handleStatusFilter = (status: ToolStatus | '') => {
    setFilters((prev) => ({
      ...prev,
      status: status || undefined,
      page: 1,
    }));
  };

  const handleTypeFilter = (toolType: ToolType | '') => {
    setFilters((prev) => ({
      ...prev,
      tool_type: toolType || undefined,
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
    return <ErrorMessage error={extractApiError(error, '加载工具列表失败')} />;
  }

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* 状态筛选 */}
          <div className="flex items-center gap-2">
            <label htmlFor="tool-status-filter" className="text-sm font-medium text-gray-700">
              状态
            </label>
            <select
              id="tool-status-filter"
              value={filters.status ?? ''}
              onChange={(e) => handleStatusFilter(e.target.value as ToolStatus | '')}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* 类型筛选 */}
          <div className="flex items-center gap-2">
            <label htmlFor="tool-type-filter" className="text-sm font-medium text-gray-700">
              类型
            </label>
            <select
              id="tool-type-filter"
              value={filters.tool_type ?? ''}
              onChange={(e) => handleTypeFilter(e.target.value as ToolType | '')}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              {TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Button size="sm" onClick={() => setRegisterOpen(true)}>
          注册工具
        </Button>
      </div>

      {/* 列表 */}
      {!data?.items.length ? (
        <div className="py-12 text-center text-gray-500" role="status">
          暂无工具
        </div>
      ) : (
        <div className="grid gap-4">
          {data.items.map((tool) => (
            <ToolCard key={tool.id} tool={tool} onSelect={onSelect} />
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

      {/* 注册对话框 */}
      <ToolRegisterDialog
        open={registerOpen}
        onClose={() => setRegisterOpen(false)}
      />
    </div>
  );
}
