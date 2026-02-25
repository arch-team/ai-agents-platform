// 部门成本报告折线图

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useCostReport } from '../api/queries';
import type { DateRangeParams } from '../api/types';

import { Card, ErrorMessage, Spinner } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

interface CostReportChartProps {
  departmentId: number;
  dateRange: DateRangeParams;
}

export function CostReportChart({ departmentId, dateRange }: CostReportChartProps) {
  const { data, isLoading, error } = useCostReport(departmentId, dateRange);

  if (isLoading) {
    return (
      <Card>
        <Spinner />
      </Card>
    );
  }
  if (error) return <ErrorMessage error={extractApiError(error, '加载成本报告失败')} />;
  if (!data || data.daily_costs.length === 0) {
    return (
      <Card>
        <h3 className="mb-2 text-lg font-semibold text-gray-900">成本趋势</h3>
        <p className="py-8 text-center text-sm text-gray-500">该时间段暂无成本数据</p>
      </Card>
    );
  }

  const chartData = data.daily_costs.map((point) => ({
    date: point.date.slice(5), // MM-DD
    cost: point.amount,
  }));

  // 每日预算均摊线 (预算 / 天数)
  const days = data.daily_costs.length || 1;
  const dailyBudget = data.budget_amount / days;

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">成本趋势</h3>
        <div className="flex gap-4 text-sm">
          <span className="text-gray-500">
            总成本: <strong className="text-gray-900">${data.total_cost.toLocaleString()}</strong>
          </span>
          <span className="text-gray-500">
            预算: <strong className="text-gray-900">${data.budget_amount.toLocaleString()}</strong>
          </span>
          <span className={data.used_percentage > 80 ? 'text-amber-600' : 'text-green-600'}>
            使用率: <strong>{data.used_percentage}%</strong>
          </span>
        </div>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `$${v}`} />
            <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`, '成本']} />
            <Legend />
            <Line
              type="monotone"
              dataKey="cost"
              name="每日成本"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
            {/* 预算基线 */}
            <Line
              type="monotone"
              dataKey={() => dailyBudget}
              name="日均预算"
              stroke="#f59e0b"
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
