// 工具详情组件

import { Card, Button, Spinner, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';

import { useTool, useSubmitTool, useDeprecateTool, useDeleteTool } from '../api/queries';
import { TOOL_TYPE_LABELS } from '../api/types';

import { ToolStatusBadge } from './ToolStatusBadge';
import { ToolApprovalPanel } from './ToolApprovalPanel';

interface ToolDetailProps {
  toolId: string;
  onBack?: () => void;
}

export function ToolDetail({ toolId, onBack }: ToolDetailProps) {
  const { data: tool, isLoading, error } = useTool(toolId);
  const submitMutation = useSubmitTool();
  const deprecateMutation = useDeprecateTool();
  const deleteMutation = useDeleteTool();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error={extractApiError(error, '加载工具详情失败')} />;
  }

  if (!tool) {
    return <ErrorMessage error="工具不存在" />;
  }

  const handleSubmit = () => submitMutation.mutate(tool.id);
  const handleDeprecate = () => deprecateMutation.mutate(tool.id);
  const handleDelete = () => {
    if (window.confirm('确定要删除这个工具吗？此操作不可撤销。')) {
      deleteMutation.mutate(tool.id, {
        onSuccess: () => onBack?.(),
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* 返回按钮 */}
      {onBack && (
        <Button variant="outline" size="sm" onClick={onBack}>
          返回列表
        </Button>
      )}

      {/* 基本信息 */}
      <Card>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold text-gray-900">{tool.name}</h2>
            <div className="flex items-center gap-3">
              <ToolStatusBadge status={tool.status} />
              <span className="text-sm text-gray-500">
                {TOOL_TYPE_LABELS[tool.tool_type] ?? tool.tool_type}
              </span>
              {tool.version && <span className="text-sm text-gray-500">v{tool.version}</span>}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2">
            {tool.status === 'draft' && (
              <Button size="sm" loading={submitMutation.isPending} onClick={handleSubmit}>
                提交审批
              </Button>
            )}
            {tool.status === 'approved' && (
              <Button
                size="sm"
                variant="outline"
                loading={deprecateMutation.isPending}
                onClick={handleDeprecate}
              >
                废弃
              </Button>
            )}
            {(tool.status === 'draft' || tool.status === 'rejected') && (
              <Button
                size="sm"
                variant="outline"
                loading={deleteMutation.isPending}
                onClick={handleDelete}
              >
                删除
              </Button>
            )}
          </div>
        </div>

        <p className="mt-4 text-sm text-gray-600">{tool.description}</p>

        {/* 元信息 */}
        <div className="mt-6 grid grid-cols-2 gap-4 border-t border-gray-100 pt-4">
          <div>
            <dt className="text-xs font-medium text-gray-500">创建者</dt>
            <dd className="mt-1 text-sm text-gray-900">{tool.created_by}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">创建时间</dt>
            <dd className="mt-1 text-sm text-gray-900">{formatDateTime(tool.created_at)}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">更新时间</dt>
            <dd className="mt-1 text-sm text-gray-900">{formatDateTime(tool.updated_at)}</dd>
          </div>
          {tool.approved_by && (
            <div>
              <dt className="text-xs font-medium text-gray-500">审批者</dt>
              <dd className="mt-1 text-sm text-gray-900">{tool.approved_by}</dd>
            </div>
          )}
        </div>

        {/* 拒绝原因 */}
        {tool.status === 'rejected' && tool.rejected_reason && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3">
            <h4 className="text-sm font-medium text-red-800">拒绝原因</h4>
            <p className="mt-1 text-sm text-red-700">{tool.rejected_reason}</p>
          </div>
        )}
      </Card>

      {/* 配置信息 */}
      {tool.configuration && Object.keys(tool.configuration).length > 0 && (
        <Card>
          <h3 className="mb-3 text-base font-semibold text-gray-900">配置信息</h3>
          <pre className="overflow-x-auto rounded-md bg-gray-50 p-4 text-sm text-gray-800">
            {JSON.stringify(tool.configuration, null, 2)}
          </pre>
        </Card>
      )}

      {/* 审批面板 */}
      <ToolApprovalPanel tool={tool} />
    </div>
  );
}
