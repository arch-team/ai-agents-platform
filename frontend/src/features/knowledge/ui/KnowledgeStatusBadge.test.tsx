import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { KnowledgeStatusBadge } from './KnowledgeStatusBadge';

describe('KnowledgeStatusBadge', () => {
  it('应显示 CREATING 状态为"创建中"', () => {
    render(<KnowledgeStatusBadge status="CREATING" />);

    expect(screen.getByText('创建中')).toBeInTheDocument();
  });

  it('应显示 ACTIVE 状态为"已激活"', () => {
    render(<KnowledgeStatusBadge status="ACTIVE" />);

    expect(screen.getByText('已激活')).toBeInTheDocument();
  });

  it('应显示 SYNCING 状态为"同步中"', () => {
    render(<KnowledgeStatusBadge status="SYNCING" />);

    expect(screen.getByText('同步中')).toBeInTheDocument();
  });

  it('应显示 FAILED 状态为"失败"', () => {
    render(<KnowledgeStatusBadge status="FAILED" />);

    expect(screen.getByText('失败')).toBeInTheDocument();
  });

  it('CREATING 状态应具有黄色样式', () => {
    render(<KnowledgeStatusBadge status="CREATING" />);

    const badge = screen.getByText('创建中');
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('ACTIVE 状态应具有绿色样式', () => {
    render(<KnowledgeStatusBadge status="ACTIVE" />);

    const badge = screen.getByText('已激活');
    expect(badge).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('SYNCING 状态应具有蓝色样式', () => {
    render(<KnowledgeStatusBadge status="SYNCING" />);

    const badge = screen.getByText('同步中');
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
  });

  it('FAILED 状态应具有红色样式', () => {
    render(<KnowledgeStatusBadge status="FAILED" />);

    const badge = screen.getByText('失败');
    expect(badge).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('应支持自定义 className', () => {
    render(<KnowledgeStatusBadge status="ACTIVE" className="extra-class" />);

    const badge = screen.getByText('已激活');
    expect(badge).toHaveClass('extra-class');
  });
});
