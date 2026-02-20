// 评估运行历史列表组件

import { useState } from 'react';

import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';
import { Spinner, ErrorMessage, Pagination } from '@/shared/ui';

import { useEvaluationRuns } from '../api/queries';
import type { EvaluationRunFilters } from '../api/types';

import { EvaluationRunStatusBadge } from './EvaluationRunStatusBadge';

interface EvaluationRunListProps {
  /** 按测试集 ID 筛选 */
  suiteId?: number;
  /** 选择运行记录 */
  onSelect?: (runId: number) => void;
}

export function EvaluationRunList({ suiteId, onSelect }: EvaluationRunListProps) {
  const [filters, setFilters] = useState<EvaluationRunFilters>({
    suite_id: suiteId,
    page: 1,
    page_size: 10,
  });
  const { data, isLoading, error } = useEvaluationRuns(filters);

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error={extractApiError(error, '加载评估运行列表失败')} />;
  }

  if (!data?.items.length) {
    return (
      <div className="py-8 text-center text-sm text-gray-500" role="status">
        暂无评估运行记录
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data.items.map((run) => {
          const passRate =
            run.total_cases > 0 ? ((run.passed_cases / run.total_cases) * 100).toFixed(1) : '0.0';

          return (
            <button
              key={run.id}
              type="button"
              className="flex w-full items-center justify-between p-4 text-left hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              onClick={() => onSelect?.(run.id)}
              aria-label={`查看评估运行 #${run.id}`}
            >
              <div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-900">运行 #{run.id}</span>
                  <EvaluationRunStatusBadge status={run.status} />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  测试集 #{run.suite_id} | Agent #{run.agent_id} | {formatDateTime(run.created_at)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">通过率 {passRate}%</p>
                <p className="text-xs text-gray-500">
                  {run.passed_cases}/{run.total_cases} 通过 | 得分 {run.score.toFixed(2)}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      <Pagination page={data.page} totalPages={data.total_pages} onPageChange={handlePageChange} />
    </div>
  );
}
