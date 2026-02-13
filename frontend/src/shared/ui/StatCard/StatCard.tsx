// 统计卡片 — 图标 + 数字 + 标签的通用展示组件

import { Card, Spinner } from '@/shared/ui';

interface StatCardProps {
  icon: React.ReactNode;
  iconBgClass: string;
  label: string;
  value: number;
  isLoading: boolean;
}

export function StatCard({ icon, iconBgClass, label, value, isLoading }: StatCardProps) {
  return (
    <Card className="flex items-center gap-4">
      <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${iconBgClass}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        {isLoading ? (
          <Spinner size="sm" />
        ) : (
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        )}
      </div>
    </Card>
  );
}
