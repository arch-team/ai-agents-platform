// 通用状态徽章组件
import { cn } from '@/shared/lib/cn';

interface StatusBadgeConfig {
  label: string;
  className: string;
}

interface StatusBadgeProps<T extends string> {
  status: T;
  config: Record<T, StatusBadgeConfig>;
  className?: string;
}

export function StatusBadge<T extends string>({ status, config, className }: StatusBadgeProps<T>) {
  const statusConfig = config[status];

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        statusConfig.className,
        className,
      )}
    >
      {statusConfig.label}
    </span>
  );
}
