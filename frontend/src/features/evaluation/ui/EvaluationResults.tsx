// 评估结果展示组件

import { cn } from '@/shared/lib/cn';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';
import { Card, Spinner, ErrorMessage } from '@/shared/ui';

import { useEvaluationRun, useEvaluationResults } from '../api/queries';
import type { EvaluationRunStatus } from '../api/types';

import { RUN_STATUS_TEXT_CONFIG } from './runStatusConfig';

interface EvaluationResultsProps {
  runId: number;
}

export function EvaluationResults({ runId }: EvaluationResultsProps) {
  const { data: run, isLoading: runLoading, error: runError } = useEvaluationRun(runId);
  const { data: resultsData, isLoading: resultsLoading } = useEvaluationResults(runId);

  if (runLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (runError || !run) {
    return <ErrorMessage error={extractApiError(runError, '加载评估运行详情失败')} />;
  }

  const statusConfig = RUN_STATUS_TEXT_CONFIG[run.status as EvaluationRunStatus] ?? {
    label: run.status,
    className: 'text-gray-600',
  };
  const passRate =
    run.total_cases > 0 ? ((run.passed_cases / run.total_cases) * 100).toFixed(1) : '0.0';

  return (
    <div className="space-y-6">
      {/* 运行概览 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">评估运行 #{run.id}</h2>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">状态</dt>
            <dd className={cn('mt-1 text-sm font-semibold', statusConfig.className)}>
              {statusConfig.label}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">通过率</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{passRate}%</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">平均得分</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{run.score.toFixed(2)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">用例统计</dt>
            <dd className="mt-1 text-sm text-gray-900">
              <span className="text-green-600">{run.passed_cases} 通过</span> /{' '}
              <span className="text-red-600">{run.failed_cases} 失败</span> / {run.total_cases} 总计
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">测试集</dt>
            <dd className="mt-1 text-sm text-gray-900">#{run.suite_id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Agent</dt>
            <dd className="mt-1 text-sm text-gray-900">#{run.agent_id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">开始时间</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {run.started_at ? formatDateTime(run.started_at) : '-'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">完成时间</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {run.completed_at ? formatDateTime(run.completed_at) : '-'}
            </dd>
          </div>
        </dl>
      </Card>

      {/* 详细结果 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">详细结果</h2>
        {resultsLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : !resultsData?.items.length ? (
          <p className="py-4 text-sm text-gray-500">暂无评估结果</p>
        ) : (
          <ul className="divide-y divide-gray-100" role="list" aria-label="评估结果列表">
            {resultsData.items.map((result) => (
              <li key={result.id} className="py-3">
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                          result.passed
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700',
                        )}
                      >
                        {result.passed ? '通过' : '未通过'}
                      </span>
                      <span className="text-sm text-gray-500">用例 #{result.case_id}</span>
                    </div>
                    <div className="mt-2">
                      <p className="text-xs font-medium text-gray-500">实际输出</p>
                      <p className="mt-0.5 whitespace-pre-wrap text-sm text-gray-700">
                        {result.actual_output || '-'}
                      </p>
                    </div>
                    {result.error_message && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-red-500">错误信息</p>
                        <p className="mt-0.5 text-sm text-red-600">{result.error_message}</p>
                      </div>
                    )}
                  </div>
                  <div className="ml-4 text-right">
                    <p className="text-sm font-medium text-gray-900">
                      得分: {result.score.toFixed(2)}
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
