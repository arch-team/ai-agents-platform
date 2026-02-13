// 模板分类筛选组件 — 7 个分类
import { cn } from '@/shared/lib/cn';

import type { TemplateCategory } from '../api/types';

// 分类配置
const CATEGORY_CONFIG: Record<TemplateCategory, { label: string }> = {
  customer_service: { label: '客户服务' },
  data_analysis: { label: '数据分析' },
  content_creation: { label: '内容创作' },
  code_assistant: { label: '编程助手' },
  research: { label: '研究助手' },
  automation: { label: '自动化' },
  other: { label: '其他' },
};

const CATEGORIES = Object.entries(CATEGORY_CONFIG) as Array<[TemplateCategory, { label: string }]>;

interface CategoryFilterProps {
  selected?: TemplateCategory;
  onChange: (category: TemplateCategory | undefined) => void;
  className?: string;
}

export function CategoryFilter({ selected, onChange, className }: CategoryFilterProps) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)} role="group" aria-label="分类筛选">
      <button
        type="button"
        onClick={() => onChange(undefined)}
        className={cn(
          'rounded-full px-3 py-1 text-sm font-medium transition-colors',
          !selected
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
        )}
        aria-pressed={!selected}
      >
        全部
      </button>
      {CATEGORIES.map(([value, config]) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(selected === value ? undefined : value)}
          className={cn(
            'rounded-full px-3 py-1 text-sm font-medium transition-colors',
            selected === value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
          )}
          aria-pressed={selected === value}
        >
          {config.label}
        </button>
      ))}
    </div>
  );
}

// 导出分类配置供外部使用
export { CATEGORY_CONFIG };
