// Agent 状态配置 — 统一 AgentCard 和 AgentStatusBadge 的样式映射

import type { AgentStatus } from './types';

/** Agent 状态显示配置 */
export const AGENT_STATUS_CONFIG: Record<AgentStatus, { label: string; className: string }> = {
  draft: { label: '草稿', className: 'bg-gray-100 text-gray-700' },
  testing: { label: '测试中', className: 'bg-blue-100 text-blue-700' },
  active: { label: '已激活', className: 'bg-green-100 text-green-700' },
  archived: { label: '已归档', className: 'bg-yellow-100 text-yellow-700' },
};
