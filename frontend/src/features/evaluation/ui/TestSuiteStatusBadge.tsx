// 测试集状态徽章组件
import { StatusBadge } from '@/shared/ui';

import type { TestSuiteStatus } from '../api/types';

const STATUS_CONFIG: Record<TestSuiteStatus, { label: string; className: string }> = {
  draft: { label: '草稿', className: 'bg-gray-100 text-gray-700' },
  active: { label: '已激活', className: 'bg-green-100 text-green-700' },
  archived: { label: '已归档', className: 'bg-yellow-100 text-yellow-700' },
};

interface TestSuiteStatusBadgeProps {
  status: TestSuiteStatus;
  className?: string;
}

export function TestSuiteStatusBadge({ status, className }: TestSuiteStatusBadgeProps) {
  return <StatusBadge status={status} config={STATUS_CONFIG} className={className} />;
}
