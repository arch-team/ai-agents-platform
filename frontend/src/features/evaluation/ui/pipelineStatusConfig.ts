// Pipeline 状态配置（共享常量文件，避免 react-refresh 警告）

import type { PipelineStatus } from '../api/types';

// 徽章样式配置
export const PIPELINE_STATUS_BADGE_CONFIG: Record<
  PipelineStatus,
  { label: string; className: string }
> = {
  scheduled: { label: '已计划', className: 'bg-blue-100 text-blue-800' },
  running: { label: '运行中', className: 'bg-yellow-100 text-yellow-800' },
  completed: { label: '已完成', className: 'bg-green-100 text-green-800' },
  failed: { label: '失败', className: 'bg-red-100 text-red-800' },
};
