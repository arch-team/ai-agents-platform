import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { StreamingIndicator } from './StreamingIndicator';

describe('StreamingIndicator', () => {
  it('应正确渲染指示器', () => {
    render(<StreamingIndicator />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('应显示 "AI 正在输入" 文本', () => {
    render(<StreamingIndicator />);

    expect(screen.getByText('AI 正在输入')).toBeInTheDocument();
  });

  it('应具有 aria-label 无障碍标签', () => {
    render(<StreamingIndicator />);

    expect(screen.getByRole('status', { name: 'AI 正在输入' })).toBeInTheDocument();
  });

  it('应渲染三个跳动的圆点动画', () => {
    render(<StreamingIndicator />);

    const statusElement = screen.getByRole('status');
    // 三个圆点在 flex gap-0.5 容器内
    const dots = statusElement.querySelectorAll('.animate-bounce');
    expect(dots).toHaveLength(3);
  });

  it('应支持自定义 className', () => {
    render(<StreamingIndicator className="custom-class" />);

    const statusElement = screen.getByRole('status');
    expect(statusElement).toHaveClass('custom-class');
  });

  it('不传 className 时应使用默认样式', () => {
    render(<StreamingIndicator />);

    const statusElement = screen.getByRole('status');
    expect(statusElement).toHaveClass('flex', 'items-center', 'gap-1');
  });
});
