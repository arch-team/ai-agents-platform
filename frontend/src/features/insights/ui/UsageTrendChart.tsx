// 使用趋势图表组件

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

import { Card, Spinner, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useUsageTrends } from '../api/queries';
import type { DateRangeParams } from '../api/types';

interface UsageTrendChartProps {
  dateRange: DateRangeParams;
}

// 格式化日期为 MM/DD 显示
function formatDateLabel(dateStr: string): string {
  const date = new Date(dateStr);
  return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`;
}

export function UsageTrendChart({ dateRange }: UsageTrendChartProps) {
  const { data, isLoading, error } = useUsageTrends(dateRange);

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
    return <ErrorMessage error={extractApiError(error, '加载使用趋势数据失败')} />;
  }

  if (!data || !data.data_points.length) {
    return (
      <Card>
        <h3 className="mb-4 text-base font-semibold text-gray-900">使用趋势</h3>
        <div className="py-8 text-center text-sm text-gray-500">暂无数据</div>
      </Card>
    );
  }

  const chartData = data.data_points.map((point) => ({
    date: formatDateLabel(point.date),
    fullDate: point.date,
    invocations: point.invocation_count,
    cost: Number(point.total_cost.toFixed(2)),
    users: point.unique_users,
  }));

  return (
    <Card>
      <h3 className="mb-4 text-base font-semibold text-gray-900">使用趋势</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} tickFormatter={(v: number) => `$${v}`} />
            <Tooltip
              labelFormatter={(_label: string, payload) => {
                const item = payload?.[0]?.payload as { fullDate?: string } | undefined;
                return item?.fullDate ?? _label;
              }}
              formatter={(value: number, name: string) => {
                const labels: Record<string, string> = {
                  invocations: '调用次数',
                  cost: '成本',
                  users: '独立用户',
                };
                const formatted = name === 'cost' ? `$${value.toFixed(2)}` : value.toLocaleString('zh-CN');
                return [formatted, labels[name] ?? name];
              }}
            />
            <Legend
              formatter={(value: string) => {
                const labels: Record<string, string> = {
                  invocations: '调用次数',
                  cost: '成本 ($)',
                  users: '独立用户',
                };
                return labels[value] ?? value;
              }}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="invocations"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cost"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="users"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
