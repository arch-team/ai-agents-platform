import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { Card } from './Card';

describe('Card', () => {
  it('应该渲染子内容', () => {
    render(<Card>卡片内容</Card>);
    expect(screen.getByText('卡片内容')).toBeInTheDocument();
  });

  it('应该应用默认样式', () => {
    render(<Card>内容</Card>);
    const card = screen.getByText('内容').closest('div');
    expect(card).toHaveClass('rounded-lg', 'border', 'bg-white', 'p-6', 'shadow-sm');
  });

  it('应该支持自定义 className', () => {
    render(<Card className="mt-4">内容</Card>);
    const card = screen.getByText('内容').closest('div');
    expect(card).toHaveClass('mt-4');
  });
});
