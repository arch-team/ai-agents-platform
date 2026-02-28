import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import type { Agent } from '../model/types';

import { AgentCard } from './AgentCard';

const mockAgent: Agent = {
  id: 1,
  name: '测试 Agent',
  description: '这是一个用于测试的 Agent',
  system_prompt: '你是一个助手',
  status: 'active',
  owner_id: 1,
  config: {
    model_id: 'claude-3',
    temperature: 0.7,
    max_tokens: 4096,
    top_p: 1,
    enable_memory: false,
  },
  created_at: '2025-01-15T00:00:00Z',
  updated_at: '2025-01-15T00:00:00Z',
};

describe('AgentCard', () => {
  it('应该显示 Agent 名称', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText('测试 Agent')).toBeInTheDocument();
  });

  it('应该显示 Agent 描述', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText('这是一个用于测试的 Agent')).toBeInTheDocument();
  });

  it('应该显示活跃状态标签', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText('已激活')).toBeInTheDocument();
  });

  it('应该显示草稿状态标签', () => {
    const draftAgent = { ...mockAgent, status: 'draft' as const };
    render(<AgentCard agent={draftAgent} />);
    expect(screen.getByText('草稿')).toBeInTheDocument();
  });

  it('应该显示已归档状态标签', () => {
    const archivedAgent = { ...mockAgent, status: 'archived' as const };
    render(<AgentCard agent={archivedAgent} />);
    expect(screen.getByText('已归档')).toBeInTheDocument();
  });

  it('应该显示创建时间', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText(/创建于/)).toBeInTheDocument();
  });

  it('应该在点击时触发 onClick', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    render(<AgentCard agent={mockAgent} onClick={handleClick} />);
    await user.click(screen.getByRole('button', { name: /查看 Agent: 测试 Agent/ }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
