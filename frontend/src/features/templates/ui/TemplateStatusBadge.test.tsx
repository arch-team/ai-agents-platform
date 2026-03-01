import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { TemplateStatusBadge } from './TemplateStatusBadge';

describe('TemplateStatusBadge', () => {
  it('应该渲染 draft 状态为"草稿"', () => {
    render(<TemplateStatusBadge status="draft" />);
    expect(screen.getByText('草稿')).toBeInTheDocument();
  });

  it('应该渲染 published 状态为"已发布"', () => {
    render(<TemplateStatusBadge status="published" />);
    expect(screen.getByText('已发布')).toBeInTheDocument();
  });

  it('应该渲染 archived 状态为"已归档"', () => {
    render(<TemplateStatusBadge status="archived" />);
    expect(screen.getByText('已归档')).toBeInTheDocument();
  });

  it('应该为 draft 状态应用灰色样式', () => {
    render(<TemplateStatusBadge status="draft" />);
    expect(screen.getByText('草稿')).toHaveClass('bg-gray-100', 'text-gray-800');
  });

  it('应该为 published 状态应用绿色样式', () => {
    render(<TemplateStatusBadge status="published" />);
    expect(screen.getByText('已发布')).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('应该为 archived 状态应用黄色样式', () => {
    render(<TemplateStatusBadge status="archived" />);
    expect(screen.getByText('已归档')).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('应该支持自定义 className', () => {
    render(<TemplateStatusBadge status="draft" className="ml-2" />);
    expect(screen.getByText('草稿')).toHaveClass('ml-2');
  });

  it('应该应用基础徽章样式', () => {
    render(<TemplateStatusBadge status="draft" />);
    expect(screen.getByText('草稿')).toHaveClass('rounded-full', 'text-xs', 'font-medium');
  });

  it('应该根据不同状态正确切换显示', () => {
    const { rerender } = render(<TemplateStatusBadge status="draft" />);
    expect(screen.getByText('草稿')).toBeInTheDocument();

    rerender(<TemplateStatusBadge status="published" />);
    expect(screen.getByText('已发布')).toBeInTheDocument();
    expect(screen.queryByText('草稿')).not.toBeInTheDocument();

    rerender(<TemplateStatusBadge status="archived" />);
    expect(screen.getByText('已归档')).toBeInTheDocument();
    expect(screen.queryByText('已发布')).not.toBeInTheDocument();
  });
});
