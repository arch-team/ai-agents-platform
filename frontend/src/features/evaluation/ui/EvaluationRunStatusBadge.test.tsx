import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { EvaluationRunStatusBadge } from './EvaluationRunStatusBadge';

describe('EvaluationRunStatusBadge', () => {
  it('应显示等待中状态', () => {
    render(<EvaluationRunStatusBadge status="pending" />);
    expect(screen.getByText('等待中')).toBeInTheDocument();
  });

  it('应显示运行中状态', () => {
    render(<EvaluationRunStatusBadge status="running" />);
    expect(screen.getByText('运行中')).toBeInTheDocument();
  });

  it('应显示已完成状态', () => {
    render(<EvaluationRunStatusBadge status="completed" />);
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('应显示失败状态', () => {
    render(<EvaluationRunStatusBadge status="failed" />);
    expect(screen.getByText('失败')).toBeInTheDocument();
  });
});
