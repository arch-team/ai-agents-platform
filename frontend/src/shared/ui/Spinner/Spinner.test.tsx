import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { Spinner } from './Spinner';

describe('Spinner', () => {
  it('应该渲染 status role', () => {
    render(<Spinner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('应该有加载中的 aria-label', () => {
    render(<Spinner />);
    expect(screen.getByLabelText('加载中')).toBeInTheDocument();
  });

  it('应该包含屏幕阅读器文本', () => {
    render(<Spinner />);
    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('应该根据 size 应用不同样式', () => {
    const { rerender } = render(<Spinner size="sm" />);
    expect(screen.getByRole('status')).toHaveClass('h-4', 'w-4');

    rerender(<Spinner size="md" />);
    expect(screen.getByRole('status')).toHaveClass('h-8', 'w-8');

    rerender(<Spinner size="lg" />);
    expect(screen.getByRole('status')).toHaveClass('h-12', 'w-12');
  });

  it('应该在 fullScreen 模式下包裹容器', () => {
    const { container } = render(<Spinner fullScreen />);
    const wrapper = container.firstElementChild;
    expect(wrapper).toHaveClass('flex', 'h-screen', 'items-center', 'justify-center');
  });

  it('应该在非 fullScreen 模式下直接渲染 spinner', () => {
    const { container } = render(<Spinner />);
    expect(container.firstElementChild).toHaveAttribute('role', 'status');
  });

  it('应该支持自定义 className', () => {
    render(<Spinner className="text-green-500" />);
    expect(screen.getByRole('status')).toHaveClass('text-green-500');
  });
});
