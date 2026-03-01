import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { TeamExecStatusBadge } from './TeamExecStatusBadge';
import type { TeamExecutionStatus } from '../api/types';

describe('TeamExecStatusBadge', () => {
  const statusLabelMap: Record<TeamExecutionStatus, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  };

  it.each(Object.entries(statusLabelMap))('应该渲染 %s 状态为 "%s"', (status, label) => {
    render(<TeamExecStatusBadge status={status as TeamExecutionStatus} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('应该对各状态应用正确的样式', () => {
    const statusStyleMap: Record<TeamExecutionStatus, string> = {
      pending: 'bg-yellow-100',
      running: 'bg-blue-100',
      completed: 'bg-green-100',
      failed: 'bg-red-100',
      cancelled: 'bg-gray-100',
    };

    (Object.keys(statusStyleMap) as TeamExecutionStatus[]).forEach((status) => {
      const { unmount } = render(<TeamExecStatusBadge status={status} />);
      expect(screen.getByText(statusLabelMap[status])).toHaveClass(statusStyleMap[status]);
      unmount();
    });
  });

  it('running 状态应包含脉动动画指示器', () => {
    const { container } = render(<TeamExecStatusBadge status="running" />);

    // 检查脉动圆点存在且带有 animate-pulse
    const pulseIndicator = container.querySelector('.animate-pulse');
    expect(pulseIndicator).toBeInTheDocument();
    expect(pulseIndicator).toHaveAttribute('aria-hidden', 'true');
  });

  it('非 running 状态不应包含脉动动画指示器', () => {
    const { container } = render(<TeamExecStatusBadge status="completed" />);

    const pulseIndicator = container.querySelector('.animate-pulse');
    expect(pulseIndicator).not.toBeInTheDocument();
  });

  it('应该支持自定义 className', () => {
    render(<TeamExecStatusBadge status="pending" className="mt-2" />);
    expect(screen.getByText('等待中')).toHaveClass('mt-2');
  });

  it('应该保留 StatusBadge 的基础样式', () => {
    render(<TeamExecStatusBadge status="completed" />);
    expect(screen.getByText('已完成')).toHaveClass('rounded-full', 'text-xs', 'font-medium');
  });
});
