// Token 消耗归因图表组件

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

// 格式化 Token 数量 (K/M)
function formatTokens(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toString();
}

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
    return <ErrorMessage error={extractApiError(error, '加载 Token 消耗归因数据失败')} />;
  }

  if (!data || !data.items.length) {
    return (
      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">Token 消耗归因</h3>
        <div className="py-8 text-center text-sm text-gray-500">暂无数据</div>
      </Card>
    );
  }

  // 按 Token 消耗降序排列，取前 10 个
  const chartData = [...data.items]
    .sort((a, b) => b.total_tokens - a.total_tokens)
    .slice(0, 10)
    .map((item) => ({
      name: item.agent_name.length > 12 ? `${item.agent_name.slice(0, 12)}...` : item.agent_name,
      fullName: item.agent_name,
      tokens: item.total_tokens,
      count: item.invocation_count,
    }));

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-900">Token 消耗归因 (Top 10)</h3>
        <span className="text-sm text-gray-500">
          总 Token: {formatTokens(data.total_tokens)}
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
            <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => formatTokens(v)} />
            <Tooltip
              formatter={(value) => [`${Number(value).toLocaleString()} Token`, 'Token 消耗']}
              labelFormatter={(_label, payload) => {
                const item = payload?.[0]?.payload as { fullName?: string } | undefined;
                return item?.fullName ?? String(_label);
              }}
            />
            <Bar dataKey="tokens" fill="#3b82f6" radius={[4, 4, 0, 0]} />
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
              <th className="py-2 text-right font-medium text-gray-500">总 Token</th>
              <th className="py-2 text-right font-medium text-gray-500">输入 Token</th>
              <th className="py-2 text-right font-medium text-gray-500">输出 Token</th>
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
                  {item.total_tokens.toLocaleString('zh-CN')}
                </td>
                <td className="py-2 text-right text-gray-600">
                  {item.tokens_input.toLocaleString('zh-CN')}
                </td>
                <td className="py-2 text-right text-gray-600">
                  {item.tokens_output.toLocaleString('zh-CN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
