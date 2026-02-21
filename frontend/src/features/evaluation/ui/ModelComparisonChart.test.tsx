import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeAll } from 'vitest';

import type { EvalPipeline } from '../api/types';

import { ModelComparisonChart } from './ModelComparisonChart';

// recharts 的 ResponsiveContainer 在 jsdom 中依赖 ResizeObserver
beforeAll(() => {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const mockCompletedPipeline: EvalPipeline = {
  id: 1,
  suite_id: 1,
  agent_id: 1,
  trigger: 'manual',
  model_ids: ['us.anthropic.claude-haiku-4-20250514-v1:0'],
  status: 'completed',
  bedrock_job_id: 'job-123',
  score_summary: { accuracy: 0.85, relevance: 0.92 },
  error_message: null,
  started_at: '2026-02-21T10:00:00Z',
  completed_at: '2026-02-21T10:15:00Z',
  created_at: '2026-02-21T10:00:00Z',
};

const mockCompletedPipeline2: EvalPipeline = {
  id: 2,
  suite_id: 1,
  agent_id: 1,
  trigger: 'manual',
  model_ids: ['us.anthropic.claude-sonnet-4-20250514-v1:0'],
  status: 'completed',
  bedrock_job_id: 'job-456',
  score_summary: { accuracy: 0.9, relevance: 0.88 },
  error_message: null,
  started_at: '2026-02-21T11:00:00Z',
  completed_at: '2026-02-21T11:15:00Z',
  created_at: '2026-02-21T11:00:00Z',
};

const mockRunningPipeline: EvalPipeline = {
  id: 3,
  suite_id: 1,
  agent_id: 1,
  trigger: 'manual',
  model_ids: ['us.anthropic.claude-haiku-4-20250514-v1:0'],
  status: 'running',
  bedrock_job_id: 'job-789',
  score_summary: {},
  error_message: null,
  started_at: '2026-02-21T12:00:00Z',
  completed_at: null,
  created_at: '2026-02-21T12:00:00Z',
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

  it('有已完成 Pipeline 时应显示图表标题', () => {
    render(<ModelComparisonChart pipelines={[mockCompletedPipeline, mockCompletedPipeline2]} />);
    // 标题应该出现两次（Card 内的 h3 和 section 的 h2），这里验证组件内的
    expect(screen.getByText('模型评分对比')).toBeInTheDocument();
  });

  it('score_summary 为空的已完成 Pipeline 不计入对比', () => {
    const emptyScorePipeline: EvalPipeline = {
      ...mockCompletedPipeline,
      id: 4,
      score_summary: {},
    };
    render(<ModelComparisonChart pipelines={[emptyScorePipeline]} />);
    expect(screen.getByText('暂无对比数据')).toBeInTheDocument();
  });

  it('混合状态 Pipeline 应正确过滤并显示图表', () => {
    render(
      <ModelComparisonChart
        pipelines={[mockCompletedPipeline, mockRunningPipeline, mockCompletedPipeline2]}
      />,
    );
    // 应该渲染图表（不显示"暂无对比数据"）
    expect(screen.queryByText('暂无对比数据')).not.toBeInTheDocument();
    expect(screen.getByText('模型评分对比')).toBeInTheDocument();
  });
});
