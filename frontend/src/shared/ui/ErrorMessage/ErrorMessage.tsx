import { cn } from '@/shared/lib/cn';

interface ErrorMessageProps {
  error: string;
  className?: string;
}

export function ErrorMessage({ error, className }: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700',
        className,
      )}
    >
      {error}
    </div>
  );
}
