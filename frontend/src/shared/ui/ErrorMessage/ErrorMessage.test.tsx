import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { ErrorMessage } from './ErrorMessage';

describe('ErrorMessage', () => {
  it('应该渲染错误消息', () => {
    render(<ErrorMessage error="发生错误" />);
    expect(screen.getByRole('alert')).toHaveTextContent('发生错误');
  });

  it('应该具有 alert role 用于无障碍', () => {
    render(<ErrorMessage error="错误" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('应该应用错误样式', () => {
    render(<ErrorMessage error="错误" />);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('text-red-700', 'bg-red-50', 'border-red-200');
  });

  it('应该支持自定义 className', () => {
    render(<ErrorMessage error="错误" className="mt-2" />);
    expect(screen.getByRole('alert')).toHaveClass('mt-2');
  });
});
