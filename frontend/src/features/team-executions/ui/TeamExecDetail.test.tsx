import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { TeamExecDetail } from './TeamExecDetail';
import type { TeamExecution } from '../api/types';

// jsdom 不支持 scrollIntoView，需要 mock
Element.prototype.scrollIntoView = vi.fn();

// Mock 数据
const mockExecution: TeamExecution = {
  id: 1,
  agent_id: 10,
  user_id: 1,
  prompt: '测试任务提示词',
  status: 'completed',
  result: '执行结果文本',
  error_message: null,
  conversation_id: 'conv-1',
  input_tokens: 100,
  output_tokens: 200,
  started_at: '2025-06-01T10:00:00Z',
  completed_at: '2025-06-01T10:05:00Z',
  created_at: '2025-06-01T10:00:00Z',
  updated_at: '2025-06-01T10:05:00Z',
};

const mockLogs = [
  {
    id: 1,
    execution_id: 1,
    sequence: 1,
    log_type: 'info',
    content: '开始执行',
    created_at: '2025-06-01T10:00:00Z',
  },
  {
    id: 2,
    execution_id: 1,
    sequence: 2,
    log_type: 'output',
    content: '执行输出结果',
    created_at: '2025-06-01T10:01:00Z',
  },
];

// Mock API hooks
let mockExecutionReturn: ReturnType<typeof vi.fn>;
let mockLogsReturn: ReturnType<typeof vi.fn>;
const mockCancelMutate = vi.fn();

vi.mock('../api/queries', () => ({
  useTeamExecution: (...args: unknown[]) => mockExecutionReturn(...args),
  useTeamExecutionLogs: (...args: unknown[]) => mockLogsReturn(...args),
  useCancelTeamExecution: () => ({
    mutate: mockCancelMutate,
    isPending: false,
  }),
}));

// Mock store hooks
vi.mock('../model/store', () => ({
  useStreamLogs: () => [],
  useIsTeamStreaming: () => false,
  useTeamExecError: () => null,
}));

// Mock TeamExecStatusBadge
vi.mock('./TeamExecStatusBadge', () => ({
  TeamExecStatusBadge: ({ status }: { status: string }) => <span>状态:{status}</span>,
}));

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('TeamExecDetail', () => {
  const defaultProps = {
    executionId: 1,
    onStartStream: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockExecutionReturn = vi.fn().mockReturnValue({
      data: mockExecution,
      isLoading: false,
    });
    mockLogsReturn = vi.fn().mockReturnValue({
      data: mockLogs,
    });
  });

  it('应该渲染 loading 状态', () => {
    mockExecutionReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('执行数据不存在时应显示错误信息', () => {
    mockExecutionReturn = vi.fn().mockReturnValue({
      data: undefined,
      isLoading: false,
    });

    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('无法加载执行详情')).toBeInTheDocument();
  });

  it('应该渲染执行概览信息', () => {
    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('执行 #1')).toBeInTheDocument();
    expect(screen.getByText('测试任务提示词')).toBeInTheDocument();
  });

  it('completed 状态下应显示执行结果', () => {
    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('执行结果')).toBeInTheDocument();
    expect(screen.getByText('执行结果文本')).toBeInTheDocument();
  });

  it('有 error_message 时应显示错误信息', () => {
    mockExecutionReturn = vi.fn().mockReturnValue({
      data: { ...mockExecution, status: 'failed', error_message: '执行失败原因' },
      isLoading: false,
    });

    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('执行失败原因')).toBeInTheDocument();
  });

  it('pending/running 状态下应显示取消执行按钮', () => {
    mockExecutionReturn = vi.fn().mockReturnValue({
      data: { ...mockExecution, status: 'running', result: null, completed_at: null },
      isLoading: false,
    });

    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByRole('button', { name: /取消执行/ })).toBeInTheDocument();
  });

  it('completed 状态下不应显示取消执行按钮', () => {
    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.queryByRole('button', { name: /取消执行/ })).not.toBeInTheDocument();
  });

  it('点击取消执行应调用 cancelMutation', async () => {
    const user = userEvent.setup();
    mockExecutionReturn = vi.fn().mockReturnValue({
      data: { ...mockExecution, status: 'pending', result: null, completed_at: null },
      isLoading: false,
    });

    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    await user.click(screen.getByRole('button', { name: /取消执行/ }));

    expect(mockCancelMutate).toHaveBeenCalledWith(1);
  });

  it('应该渲染日志内容', () => {
    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('执行日志')).toBeInTheDocument();
    expect(screen.getByText('开始执行')).toBeInTheDocument();
    expect(screen.getByText('执行输出结果')).toBeInTheDocument();
  });

  it('无日志时应显示空状态', () => {
    mockLogsReturn = vi.fn().mockReturnValue({
      data: [],
    });

    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('暂无日志')).toBeInTheDocument();
  });

  it('日志区域应有正确的 ARIA 属性', () => {
    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    const logRegion = screen.getByRole('log', { name: '执行日志' });
    expect(logRegion).toBeInTheDocument();
    expect(logRegion).toHaveAttribute('aria-live', 'polite');
  });

  it('completed 状态无结果文本时应显示默认提示', () => {
    mockExecutionReturn = vi.fn().mockReturnValue({
      data: { ...mockExecution, result: null },
      isLoading: false,
    });

    render(<TeamExecDetail {...defaultProps} />, { wrapper: Wrapper });

    expect(screen.getByText('执行已完成，无文本输出')).toBeInTheDocument();
  });
});
