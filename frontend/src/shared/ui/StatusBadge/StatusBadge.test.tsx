import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { StatusBadge } from './StatusBadge';

type TestStatus = 'active' | 'inactive';

const testConfig: Record<TestStatus, { label: string; className: string }> = {
  active: { label: '活跃', className: 'bg-green-100 text-green-700' },
  inactive: { label: '未激活', className: 'bg-gray-100 text-gray-700' },
};

describe('StatusBadge', () => {
  it('应该渲染对应状态的标签', () => {
    render(<StatusBadge status="active" config={testConfig} />);
    expect(screen.getByText('活跃')).toBeInTheDocument();
  });

  it('应该应用对应状态的样式', () => {
    render(<StatusBadge status="active" config={testConfig} />);
    expect(screen.getByText('活跃')).toHaveClass('bg-green-100', 'text-green-700');
  });

  it('应该根据不同状态切换显示', () => {
    const { rerender } = render(<StatusBadge status="active" config={testConfig} />);
    expect(screen.getByText('活跃')).toBeInTheDocument();

    rerender(<StatusBadge status="inactive" config={testConfig} />);
    expect(screen.getByText('未激活')).toBeInTheDocument();
    expect(screen.getByText('未激活')).toHaveClass('bg-gray-100', 'text-gray-700');
  });

  it('应该支持自定义 className', () => {
    render(<StatusBadge status="active" config={testConfig} className="ml-2" />);
    expect(screen.getByText('活跃')).toHaveClass('ml-2');
  });

  it('应该应用基础徽章样式', () => {
    render(<StatusBadge status="active" config={testConfig} />);
    expect(screen.getByText('活跃')).toHaveClass('rounded-full', 'text-xs', 'font-medium');
  });
});
