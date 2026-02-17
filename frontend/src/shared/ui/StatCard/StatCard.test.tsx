import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { StatCard } from './StatCard';

describe('StatCard', () => {
  const defaultProps = {
    icon: <span data-testid="icon">图标</span>,
    iconBgClass: 'bg-blue-100',
    label: '总数',
    value: 42,
    isLoading: false,
  };

  it('应该渲染标签和数值', () => {
    render(<StatCard {...defaultProps} />);
    expect(screen.getByText('总数')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('应该渲染图标', () => {
    render(<StatCard {...defaultProps} />);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('应该在加载时显示 Spinner', () => {
    render(<StatCard {...defaultProps} isLoading={true} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByText('42')).not.toBeInTheDocument();
  });

  it('应该在非加载时显示数值而非 Spinner', () => {
    render(<StatCard {...defaultProps} isLoading={false} />);
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
