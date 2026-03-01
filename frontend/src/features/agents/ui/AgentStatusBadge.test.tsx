import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { AgentStatusBadge } from './AgentStatusBadge';
import type { AgentStatus } from '@/entities/agent';

describe('AgentStatusBadge', () => {
  const statusLabelMap: Record<AgentStatus, string> = {
    draft: '草稿',
    active: '已激活',
    archived: '已归档',
  };

  it.each(Object.entries(statusLabelMap))('应该渲染 %s 状态为 "%s"', (status, label) => {
    render(<AgentStatusBadge status={status as AgentStatus} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('应该对各状态应用正确的样式', () => {
    const statusStyleMap: Record<AgentStatus, string> = {
      draft: 'bg-gray-100',
      active: 'bg-green-100',
      archived: 'bg-yellow-100',
    };

    (Object.keys(statusStyleMap) as AgentStatus[]).forEach((status) => {
      const { unmount } = render(<AgentStatusBadge status={status} />);
      expect(screen.getByText(statusLabelMap[status])).toHaveClass(statusStyleMap[status]);
      unmount();
    });
  });

  it('应该支持自定义 className', () => {
    render(<AgentStatusBadge status="active" className="ml-2" />);
    expect(screen.getByText('已激活')).toHaveClass('ml-2');
  });

  it('应该保留 StatusBadge 的基础样式', () => {
    render(<AgentStatusBadge status="draft" />);
    expect(screen.getByText('草稿')).toHaveClass('rounded-full', 'text-xs', 'font-medium');
  });

  it('应该正确切换状态显示', () => {
    const { rerender } = render(<AgentStatusBadge status="draft" />);
    expect(screen.getByText('草稿')).toBeInTheDocument();

    rerender(<AgentStatusBadge status="active" />);
    expect(screen.getByText('已激活')).toBeInTheDocument();
    expect(screen.queryByText('草稿')).not.toBeInTheDocument();

    rerender(<AgentStatusBadge status="archived" />);
    expect(screen.getByText('已归档')).toBeInTheDocument();
    expect(screen.queryByText('已激活')).not.toBeInTheDocument();
  });
});
