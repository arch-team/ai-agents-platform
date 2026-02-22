// 模型评分对比柱状图组件（占位）
// 当前后端 Pipeline DTO 尚未返回 score_summary，后续迭代补充

import { Card } from '@/shared/ui';

import type { EvalPipeline } from '../api/types';

interface ModelComparisonChartProps {
  /** Pipeline 列表数据 */
  pipelines: EvalPipeline[];
}

export function ModelComparisonChart({ pipelines }: ModelComparisonChartProps) {
  const completedCount = pipelines.filter((p) => p.status === 'completed').length;

  if (completedCount === 0) {
    return (
      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">模型评分对比</h3>
        <div className="py-8 text-center text-sm text-gray-500">暂无对比数据</div>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-4 text-base font-semibold text-gray-900">模型评分对比</h3>
      <div className="py-8 text-center text-sm text-gray-500">
        已完成 {completedCount} 个 Pipeline，评分对比功能将在后续版本中提供
      </div>
    </Card>
  );
}
