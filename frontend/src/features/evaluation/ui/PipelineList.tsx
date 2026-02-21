// Pipeline 运行历史列表组件

import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';
import { Button, Spinner, ErrorMessage, Card } from '@/shared/ui';

import { useEvalPipelines, useTriggerPipeline } from '../api/queries';

import { PipelineStatusBadge } from './PipelineStatusBadge';

interface PipelineListProps {
  /** 测试集 ID */
  suiteId: number;
}

/** 格式化评分摘要为可读字符串 */
function formatScoreSummary(scoreSummary: Record<string, number>): string {
  const entries = Object.entries(scoreSummary);
  if (entries.length === 0) return '-';
  return entries.map(([key, value]) => `${key}: ${value.toFixed(2)}`).join(', ');
}

/** 截断模型 ID 显示 */
function formatModelIds(modelIds: string[]): string {
  if (modelIds.length === 0) return '-';
  // 截取模型名称最后部分便于展示
  return modelIds
    .map((id) => {
      const parts = id.split('.');
      return parts.length > 1 ? parts.slice(1).join('.') : id;
    })
    .join(', ');
}

export function PipelineList({ suiteId }: PipelineListProps) {
  const { data: pipelines, isLoading, error } = useEvalPipelines(suiteId);
  const triggerMutation = useTriggerPipeline();

  const handleTrigger = () => {
    triggerMutation.mutate({ suiteId });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error={extractApiError(error, '加载 Pipeline 列表失败')} />;
  }

  return (
    <div className="space-y-4">
      {/* 操作栏 */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">共 {pipelines?.length ?? 0} 条 Pipeline 记录</p>
        <Button onClick={handleTrigger} disabled={triggerMutation.isPending}>
          {triggerMutation.isPending ? '触发中...' : '触发评估'}
        </Button>
      </div>

      {/* 触发错误提示 */}
      {triggerMutation.error && (
        <ErrorMessage error={extractApiError(triggerMutation.error, '触发 Pipeline 失败')} />
      )}

      {/* 空状态 */}
      {(!pipelines || pipelines.length === 0) && (
        <Card>
          <div className="py-8 text-center text-sm text-gray-500" role="status">
            暂无 Pipeline 记录，点击"触发评估"开始
          </div>
        </Card>
      )}

      {/* Pipeline 列表 */}
      {pipelines && pipelines.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 font-medium text-gray-500">ID</th>
                <th className="px-4 py-3 font-medium text-gray-500">状态</th>
                <th className="px-4 py-3 font-medium text-gray-500">触发方式</th>
                <th className="px-4 py-3 font-medium text-gray-500">模型</th>
                <th className="px-4 py-3 font-medium text-gray-500">评分摘要</th>
                <th className="px-4 py-3 font-medium text-gray-500">创建时间</th>
              </tr>
            </thead>
            <tbody>
              {pipelines.map((pipeline) => (
                <tr key={pipeline.id} className="border-b border-gray-100">
                  <td className="px-4 py-3 text-gray-900">#{pipeline.id}</td>
                  <td className="px-4 py-3">
                    <PipelineStatusBadge status={pipeline.status} />
                  </td>
                  <td className="px-4 py-3 text-gray-600">{pipeline.trigger}</td>
                  <td className="px-4 py-3 text-gray-600">
                    <span title={pipeline.model_ids.join(', ')}>
                      {formatModelIds(pipeline.model_ids)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {formatScoreSummary(pipeline.score_summary)}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatDateTime(pipeline.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
