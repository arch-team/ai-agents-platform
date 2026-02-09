import { cn } from '@/shared/lib/cn';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
  className?: string;
}

const sizeStyles: Record<string, string> = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-3',
  lg: 'h-12 w-12 border-4',
};

export function Spinner({ size = 'md', fullScreen = false, className }: SpinnerProps) {
  const spinner = (
    <div
      role="status"
      aria-label="加载中"
      className={cn(
        'animate-spin rounded-full border-solid border-gray-300 border-t-blue-600',
        sizeStyles[size],
        className,
      )}
    >
      <span className="sr-only">加载中...</span>
    </div>
  );

  if (fullScreen) {
    return <div className="flex h-screen w-full items-center justify-center">{spinner}</div>;
  }

  return spinner;
}
