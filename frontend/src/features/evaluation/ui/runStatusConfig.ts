// 评估运行状态配置（共享常量文件，避免 react-refresh 警告）

import type { EvaluationRunStatus } from '../api/types';

// 徽章样式配置（用于列表等场景）
export const RUN_STATUS_BADGE_CONFIG: Record<EvaluationRunStatus, { label: string; className: string }> = {
  pending: { label: '等待中', className: 'bg-gray-100 text-gray-700' },
  running: { label: '运行中', className: 'bg-blue-100 text-blue-700' },
  completed: { label: '已完成', className: 'bg-green-100 text-green-700' },
  failed: { label: '失败', className: 'bg-red-100 text-red-700' },
};

// 文本样式配置（用于详情等场景）
export const RUN_STATUS_TEXT_CONFIG: Record<EvaluationRunStatus, { label: string; className: string }> = {
  pending: { label: '等待中', className: 'text-gray-600' },
  running: { label: '运行中', className: 'text-blue-600' },
  completed: { label: '已完成', className: 'text-green-600' },
  failed: { label: '失败', className: 'text-red-600' },
};
