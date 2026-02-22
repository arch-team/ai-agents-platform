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
                <th className="px-4 py-3 font-medium text-gray-500">Bedrock Job</th>
                <th className="px-4 py-3 font-medium text-gray-500">开始时间</th>
                <th className="px-4 py-3 font-medium text-gray-500">完成时间</th>
              </tr>
            </thead>
            <tbody>
              {pipelines.map((pipeline) => (
                <tr key={pipeline.id} className="border-b border-gray-100">
                  <td className="px-4 py-3 font-mono text-xs text-gray-900">
                    {pipeline.id.slice(0, 8)}
                  </td>
                  <td className="px-4 py-3">
                    <PipelineStatusBadge status={pipeline.status} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">
                    {pipeline.bedrock_job_id ?? '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatDateTime(pipeline.started_at)}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {pipeline.completed_at ? formatDateTime(pipeline.completed_at) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
