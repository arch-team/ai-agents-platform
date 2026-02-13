// 概览统计卡片组件

import { Card, Spinner, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useInsightsSummary } from '../api/queries';
import type { DateRangeParams } from '../api/types';

// 统计指标项
interface MetricCardProps {
  label: string;
  value: string | number;
  subLabel?: string;
}

function MetricCard({ label, value, subLabel }: MetricCardProps) {
  return (
    <Card className="flex flex-col">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold text-gray-900">{value}</dd>
      {subLabel && <dd className="mt-1 text-xs text-gray-400">{subLabel}</dd>}
    </Card>
  );
}

// 格式化货币
function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`;
}

// 格式化大数字
function formatNumber(value: number): string {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }
  return value.toLocaleString('zh-CN');
}

interface InsightsSummaryProps {
  dateRange: DateRangeParams;
}

export function InsightsSummary({ dateRange }: InsightsSummaryProps) {
  const { data, isLoading, error } = useInsightsSummary(dateRange);

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error={extractApiError(error, '加载概览统计失败')} />;
  }

  if (!data) return null;

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
      <MetricCard
        label="Agent 总数"
        value={data.total_agents}
        subLabel={`${data.active_agents} 个活跃`}
      />
      <MetricCard
        label="调用总量"
        value={formatNumber(data.total_invocations)}
      />
      <MetricCard
        label="总成本"
        value={formatCurrency(data.total_cost)}
      />
      <MetricCard
        label="平均响应时间"
        value={`${data.avg_response_time_ms}ms`}
      />
      <MetricCard
        label="活跃 Agent"
        value={data.active_agents}
        subLabel={`共 ${data.total_agents} 个`}
      />
    </div>
  );
}
