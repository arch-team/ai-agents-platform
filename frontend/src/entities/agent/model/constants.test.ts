import { describe, it, expect } from 'vitest';

import { AGENT_STATUS_CONFIG } from './constants';

describe('AGENT_STATUS_CONFIG', () => {
  it('应该包含 draft 状态配置', () => {
    expect(AGENT_STATUS_CONFIG.draft).toEqual({
      label: '草稿',
      className: 'bg-gray-100 text-gray-700',
    });
  });

  it('应该包含 active 状态配置', () => {
    expect(AGENT_STATUS_CONFIG.active).toEqual({
      label: '已激活',
      className: 'bg-green-100 text-green-700',
    });
  });

  it('应该包含 archived 状态配置', () => {
    expect(AGENT_STATUS_CONFIG.archived).toEqual({
      label: '已归档',
      className: 'bg-yellow-100 text-yellow-700',
    });
  });

  it('应该包含且仅包含三种状态', () => {
    const statuses = Object.keys(AGENT_STATUS_CONFIG);
    expect(statuses).toHaveLength(3);
    expect(statuses).toEqual(expect.arrayContaining(['draft', 'active', 'archived']));
  });
});
