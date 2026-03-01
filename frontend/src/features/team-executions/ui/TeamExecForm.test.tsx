import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { TeamExecForm } from './TeamExecForm';
import type { Agent } from '@/entities/agent';

// 构造测试用 Agent 数据
const mockAgents: Agent[] = [
  {
    id: 1,
    name: 'Agent Alpha',
    description: '描述A',
    system_prompt: '提示词A',
    status: 'active',
    owner_id: 1,
    config: {
      model_id: 'model-1',
      temperature: 0.7,
      max_tokens: 2048,
      top_p: 1,
      enable_memory: false,
    },
    tool_ids: [],
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  },
  {
    id: 2,
    name: 'Agent Beta',
    description: '描述B',
    system_prompt: '提示词B',
    status: 'active',
    owner_id: 1,
    config: {
      model_id: 'model-2',
      temperature: 0.5,
      max_tokens: 1024,
      top_p: 1,
      enable_memory: false,
    },
    tool_ids: [],
    created_at: '2025-01-02',
    updated_at: '2025-01-02',
  },
  {
    id: 3,
    name: 'Agent Inactive',
    description: '未激活',
    system_prompt: '提示词C',
    status: 'draft',
    owner_id: 1,
    config: {
      model_id: 'model-1',
      temperature: 0.7,
      max_tokens: 2048,
      top_p: 1,
      enable_memory: false,
    },
    tool_ids: [],
    created_at: '2025-01-03',
    updated_at: '2025-01-03',
  },
];

describe('TeamExecForm', () => {
  const defaultProps = {
    agents: mockAgents,
    selectedAgentId: null as number | null,
    onSelectAgent: vi.fn(),
    onSubmit: vi.fn(),
    isSubmitting: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该渲染表单基本元素', () => {
    render(<TeamExecForm {...defaultProps} />);

    expect(screen.getByLabelText('选择 Agent')).toBeInTheDocument();
    expect(screen.getByLabelText('执行提示词')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '提交执行' })).toBeInTheDocument();
  });

  it('应该只显示 active 状态的 Agent', () => {
    render(<TeamExecForm {...defaultProps} />);

    screen.getByLabelText('选择 Agent');
    // active Agent 应可选
    expect(screen.getByRole('option', { name: 'Agent Alpha' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Agent Beta' })).toBeInTheDocument();
    // draft Agent 不应显示在选项中
    expect(screen.queryByRole('option', { name: 'Agent Inactive' })).not.toBeInTheDocument();
  });

  it('没有 active Agent 时应显示提示信息', () => {
    const draftOnlyAgents = mockAgents.filter((a) => a.status === 'draft');
    render(<TeamExecForm {...defaultProps} agents={draftOnlyAgents} />);

    expect(screen.getByText(/暂无可用的 Agent/)).toBeInTheDocument();
  });

  it('未选择 Agent 时提交按钮应禁用', () => {
    render(<TeamExecForm {...defaultProps} selectedAgentId={null} />);

    expect(screen.getByRole('button', { name: '提交执行' })).toBeDisabled();
  });

  it('选择 Agent 后应调用 onSelectAgent', async () => {
    const user = userEvent.setup();
    render(<TeamExecForm {...defaultProps} />);

    await user.selectOptions(screen.getByLabelText('选择 Agent'), '1');

    expect(defaultProps.onSelectAgent).toHaveBeenCalledWith(1);
  });

  it('应该正确提交表单', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<TeamExecForm {...defaultProps} selectedAgentId={1} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText('执行提示词'), '请执行任务');
    await user.click(screen.getByRole('button', { name: '提交执行' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith('请执行任务');
    });
  });

  it('提示词为空时提交应显示验证错误', async () => {
    const user = userEvent.setup();
    render(<TeamExecForm {...defaultProps} selectedAgentId={1} />);

    await user.click(screen.getByRole('button', { name: '提交执行' }));

    await waitFor(() => {
      expect(screen.getByText('请输入执行提示词')).toBeInTheDocument();
    });
  });

  it('isSubmitting 为 true 时提交按钮应禁用', () => {
    render(<TeamExecForm {...defaultProps} selectedAgentId={1} isSubmitting={true} />);

    // loading 状态下 Button 内含 Spinner（sr-only "加载中..."），accessible name 包含该文本
    const submitButton = screen.getByRole('button', { name: /提交执行/ });
    expect(submitButton).toBeDisabled();
  });

  it('提交成功后应重置表单', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<TeamExecForm {...defaultProps} selectedAgentId={1} onSubmit={onSubmit} />);

    const textarea = screen.getByLabelText('执行提示词');
    await user.type(textarea, '请执行任务');
    await user.click(screen.getByRole('button', { name: '提交执行' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    });

    // 提交后表单应该被重置
    await waitFor(() => {
      expect(textarea).toHaveValue('');
    });
  });
});
