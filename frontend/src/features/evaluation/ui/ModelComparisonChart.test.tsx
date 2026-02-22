import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import type { EvalPipeline } from '../api/types';

import { ModelComparisonChart } from './ModelComparisonChart';

const mockCompletedPipeline: EvalPipeline = {
  id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
  eval_suite_id: '1',
  status: 'completed',
  bedrock_job_id: 'job-123',
  started_at: '2026-02-21T10:00:00Z',
  completed_at: '2026-02-21T10:15:00Z',
};

const mockRunningPipeline: EvalPipeline = {
  id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
  eval_suite_id: '1',
  status: 'running',
  bedrock_job_id: 'job-789',
  started_at: '2026-02-21T12:00:00Z',
  completed_at: null,
};

describe('ModelComparisonChart', () => {
  it('空数据时应显示暂无对比数据', () => {
    render(<ModelComparisonChart pipelines={[]} />);
    expect(screen.getByText('暂无对比数据')).toBeInTheDocument();
  });

  it('仅有运行中 Pipeline 时应显示暂无对比数据', () => {
    render(<ModelComparisonChart pipelines={[mockRunningPipeline]} />);
    expect(screen.getByText('暂无对比数据')).toBeInTheDocument();
  });

  it('有已完成 Pipeline 时应显示占位提示', () => {
    render(<ModelComparisonChart pipelines={[mockCompletedPipeline]} />);
    expect(screen.getByText('模型评分对比')).toBeInTheDocument();
    expect(screen.getByText(/已完成 1 个 Pipeline/)).toBeInTheDocument();
  });

  it('混合状态 Pipeline 应只计入已完成的数量', () => {
    render(<ModelComparisonChart pipelines={[mockCompletedPipeline, mockRunningPipeline]} />);
    expect(screen.getByText(/已完成 1 个 Pipeline/)).toBeInTheDocument();
    expect(screen.queryByText('暂无对比数据')).not.toBeInTheDocument();
  });
});
