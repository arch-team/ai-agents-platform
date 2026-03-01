import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { PipelineStatusBadge } from './PipelineStatusBadge';
import type { PipelineStatus } from '../api/types';

describe('PipelineStatusBadge', () => {
  it('应该渲染 pending 状态', () => {
    render(<PipelineStatusBadge status="pending" />);
    expect(screen.getByText('等待中')).toBeInTheDocument();
  });

  it('应该渲染 running 状态', () => {
    render(<PipelineStatusBadge status="running" />);
    expect(screen.getByText('运行中')).toBeInTheDocument();
  });

  it('应该渲染 completed 状态', () => {
    render(<PipelineStatusBadge status="completed" />);
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('应该渲染 failed 状态', () => {
    render(<PipelineStatusBadge status="failed" />);
    expect(screen.getByText('失败')).toBeInTheDocument();
  });

  it('应该对不同状态应用正确的样式', () => {
    const statusStyleMap: Record<PipelineStatus, string> = {
      pending: 'bg-blue-100',
      running: 'bg-yellow-100',
      completed: 'bg-green-100',
      failed: 'bg-red-100',
    };

    const { rerender } = render(<PipelineStatusBadge status="pending" />);
    expect(screen.getByText('等待中')).toHaveClass(statusStyleMap.pending);

    rerender(<PipelineStatusBadge status="running" />);
    expect(screen.getByText('运行中')).toHaveClass(statusStyleMap.running);

    rerender(<PipelineStatusBadge status="completed" />);
    expect(screen.getByText('已完成')).toHaveClass(statusStyleMap.completed);

    rerender(<PipelineStatusBadge status="failed" />);
    expect(screen.getByText('失败')).toHaveClass(statusStyleMap.failed);
  });

  it('应该支持自定义 className', () => {
    render(<PipelineStatusBadge status="pending" className="ml-4" />);
    expect(screen.getByText('等待中')).toHaveClass('ml-4');
  });

  it('应该保留 StatusBadge 的基础样式', () => {
    render(<PipelineStatusBadge status="completed" />);
    expect(screen.getByText('已完成')).toHaveClass('rounded-full', 'text-xs', 'font-medium');
  });
});
