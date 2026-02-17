import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { TestSuiteStatusBadge } from './TestSuiteStatusBadge';

describe('TestSuiteStatusBadge', () => {
  it('应显示草稿状态', () => {
    render(<TestSuiteStatusBadge status="draft" />);
    expect(screen.getByText('草稿')).toBeInTheDocument();
  });

  it('应显示已激活状态', () => {
    render(<TestSuiteStatusBadge status="active" />);
    expect(screen.getByText('已激活')).toBeInTheDocument();
  });

  it('应显示已归档状态', () => {
    render(<TestSuiteStatusBadge status="archived" />);
    expect(screen.getByText('已归档')).toBeInTheDocument();
  });
});
