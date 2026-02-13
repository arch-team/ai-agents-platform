// Insights 仪表板页面
import { useState } from 'react';

import {
  InsightsSummary,
  CostBreakdownChart,
  UsageTrendChart,
  DateRangePicker,
} from '@/features/insights';
import type { DateRangeParams } from '@/features/insights';

// 默认时间范围: 最近 30 天
function getDefaultDateRange(): DateRangeParams {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  return {
    start_date: start.toISOString().split('T')[0],
    end_date: end.toISOString().split('T')[0],
  };
}

export default function InsightsPage() {
  const [dateRange, setDateRange] = useState<DateRangeParams>(getDefaultDateRange);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Insights 仪表板</h1>
        <DateRangePicker
          startDate={dateRange.start_date}
          endDate={dateRange.end_date}
          onStartDateChange={(date) =>
            setDateRange((prev) => ({ ...prev, start_date: date }))
          }
          onEndDateChange={(date) =>
            setDateRange((prev) => ({ ...prev, end_date: date }))
          }
        />
      </div>

      {/* 概览统计 */}
      <InsightsSummary dateRange={dateRange} />

      {/* 图表区域 */}
      <div className="space-y-6">
        <UsageTrendChart dateRange={dateRange} />
        <CostBreakdownChart dateRange={dateRange} />
      </div>
    </div>
  );
}
