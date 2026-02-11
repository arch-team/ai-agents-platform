// 通用分页组件

import { forwardRef } from 'react';

import { cn } from '@/shared/lib/cn';

import { Button } from '../Button';

interface PaginationProps {
  /** 当前页码 */
  page: number;
  /** 总页数 */
  totalPages: number;
  /** 页码变更回调 */
  onPageChange: (page: number) => void;
  /** 自定义 className */
  className?: string;
}

export const Pagination = forwardRef<HTMLElement, PaginationProps>(
  ({ page, totalPages, onPageChange, className }, ref) => {
    if (totalPages <= 1) {
      return null;
    }

    return (
      <nav
        ref={ref}
        aria-label="分页导航"
        className={cn('flex items-center justify-center gap-2', className)}
      >
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="上一页"
        >
          上一页
        </Button>
        <span className="text-sm text-gray-600">
          第 {page} / {totalPages} 页
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="下一页"
        >
          下一页
        </Button>
      </nav>
    );
  },
);
Pagination.displayName = 'Pagination';
