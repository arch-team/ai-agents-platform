// 时间范围选择组件

import { cn } from '@/shared/lib/cn';

// 预设时间范围选项
const PRESET_RANGES = [
  { label: '最近 7 天', days: 7 },
  { label: '最近 14 天', days: 14 },
  { label: '最近 30 天', days: 30 },
  { label: '最近 90 天', days: 90 },
] as const;

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  className?: string;
}

// 获取相对日期 (YYYY-MM-DD 格式)
function getRelativeDate(daysAgo: number): string {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString().split('T')[0];
}

// 获取今天日期 (YYYY-MM-DD 格式)
function getToday(): string {
  return new Date().toISOString().split('T')[0];
}

export function DateRangePicker({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  className,
}: DateRangePickerProps) {
  const handlePresetClick = (days: number) => {
    onStartDateChange(getRelativeDate(days));
    onEndDateChange(getToday());
  };

  return (
    <div className={cn('flex flex-wrap items-center gap-3', className)}>
      {/* 预设按钮 */}
      <div className="flex gap-1">
        {PRESET_RANGES.map((preset) => (
          <button
            key={preset.days}
            type="button"
            onClick={() => handlePresetClick(preset.days)}
            className={cn(
              'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
              startDate === getRelativeDate(preset.days) && endDate === getToday()
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
            )}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* 自定义日期选择 */}
      <div className="flex items-center gap-2">
        <label htmlFor="start-date" className="text-xs text-gray-500">
          从
        </label>
        <input
          id="start-date"
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        />
        <label htmlFor="end-date" className="text-xs text-gray-500">
          至
        </label>
        <input
          id="end-date"
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        />
      </div>
    </div>
  );
}
