// 成本归因图表组件

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import { Card, Spinner, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useCostBreakdown } from '../api/queries';
import type { DateRangeParams } from '../api/types';

interface CostBreakdownChartProps {
  dateRange: DateRangeParams;
}

export function CostBreakdownChart({ dateRange }: CostBreakdownChartProps) {
  const { data, isLoading, error } = useCostBreakdown(dateRange);

  if (isLoading) {
    return (
      <Card>
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      </Card>
    );
  }

  if (error) {
    return <ErrorMessage error={extractApiError(error, '加载成本归因数据失败')} />;
  }

  if (!data || !data.items.length) {
    return (
      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">成本归因</h3>
        <div className="py-8 text-center text-sm text-gray-500">暂无数据</div>
      </Card>
    );
  }

  // 按成本降序排列，取前 10 个
  const chartData = [...data.items]
    .sort((a, b) => b.total_cost - a.total_cost)
    .slice(0, 10)
    .map((item) => ({
      name: item.agent_name.length > 12 ? `${item.agent_name.slice(0, 12)}...` : item.agent_name,
      fullName: item.agent_name,
      cost: Number(item.total_cost.toFixed(2)),
      count: item.invocation_count,
    }));

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-900">成本归因 (Top 10)</h3>
        <span className="text-sm text-gray-500">
          总成本: ${data.total_cost.toFixed(2)}
        </span>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
              angle={-30}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `$${v}`} />
            <Tooltip
              formatter={(value: number) => [`$${value.toFixed(2)}`, '成本']}
              labelFormatter={(label: string, payload) => {
                const item = payload?.[0]?.payload as { fullName?: string } | undefined;
                return item?.fullName ?? label;
              }}
            />
            <Bar dataKey="cost" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 详细表格 */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="py-2 font-medium text-gray-500">Agent</th>
              <th className="py-2 text-right font-medium text-gray-500">调用次数</th>
              <th className="py-2 text-right font-medium text-gray-500">总成本</th>
              <th className="py-2 text-right font-medium text-gray-500">平均成本</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.agent_id} className="border-b border-gray-100">
                <td className="py-2 text-gray-900">{item.agent_name}</td>
                <td className="py-2 text-right text-gray-600">
                  {item.invocation_count.toLocaleString('zh-CN')}
                </td>
                <td className="py-2 text-right text-gray-600">
                  ${item.total_cost.toFixed(2)}
                </td>
                <td className="py-2 text-right text-gray-600">
                  ${item.avg_cost_per_invocation.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
