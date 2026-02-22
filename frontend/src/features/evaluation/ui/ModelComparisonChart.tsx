// 模型评分对比柱状图组件

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

import { Card } from '@/shared/ui';

import type { EvalPipeline } from '../api/types';

// 预定义颜色序列，用于不同评分维度
const BAR_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

interface ModelComparisonChartProps {
  /** Pipeline 列表数据 */
  pipelines: EvalPipeline[];
}

export function ModelComparisonChart({ pipelines }: ModelComparisonChartProps) {
  // 过滤出有评分数据的已完成 Pipeline
  const completedPipelines = useMemo(
    () =>
      pipelines.filter((p) => p.status === 'completed' && Object.keys(p.score_summary).length > 0),
    [pipelines],
  );

  // 收集所有评分维度 key
  const scoreKeys = useMemo(() => {
    const keys = new Set<string>();
    completedPipelines.forEach((p) => {
      Object.keys(p.score_summary).forEach((k) => keys.add(k));
    });
    return Array.from(keys);
  }, [completedPipelines]);

  // 构建图表数据
  const chartData = useMemo(
    () =>
      completedPipelines.map((p) => {
        // 使用模型名称或 Pipeline ID 作为标签
        const label =
          p.model_ids.length > 0
            ? p.model_ids
                .map((id) => {
                  const parts = id.split('.');
                  return parts.length > 1 ? parts.slice(1).join('.') : id;
                })
                .join(', ')
            : `Pipeline #${p.id}`;

        const entry: Record<string, string | number> = { name: label };
        scoreKeys.forEach((key) => {
          entry[key] = p.score_summary[key] ?? 0;
        });
        return entry;
      }),
    [completedPipelines, scoreKeys],
  );

  // 无数据状态
  if (completedPipelines.length === 0 || scoreKeys.length === 0) {
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
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
              angle={-15}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fontSize: 12 }} domain={[0, 1]} />
            <Tooltip
              formatter={(value: number | string | undefined) =>
                typeof value === 'number' ? value.toFixed(2) : (value ?? '')
              }
            />
            <Legend />
            {scoreKeys.map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={BAR_COLORS[index % BAR_COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
