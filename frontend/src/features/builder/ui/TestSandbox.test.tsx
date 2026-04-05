// TestSandbox 组件单元测试 — 真实执行集成

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';

import { useBuilderStore } from '../model/store';

import { TestSandbox } from './TestSandbox';

// ── Mock 依赖 ──

// mock useAgent（来自 agents feature）
const mockUseAgent = vi.fn();
vi.mock('@/features/agents', () => ({
  useAgent: (...args: unknown[]) => mockUseAgent(...args),
}));

// mock apiClient（对话创建）
const mockPost = vi.fn();
vi.mock('@/shared/api', () => ({
  apiClient: { post: (...args: unknown[]) => mockPost(...args) },
}));

// mock parseSSEStream（SSE 流式消息）
const mockParseSSEStream = vi.fn();
vi.mock('@/shared/lib/parseSSEStream', () => ({
  parseSSEStream: (...args: unknown[]) => mockParseSSEStream(...args),
}));

// mock env
vi.mock('@/shared/config/env', () => ({
  env: { VITE_API_BASE_URL: 'http://localhost:8000' },
}));

// ── 辅助函数 ──

// 创建 mock async generator
async function* createMockSSEStream(
  chunks: Array<{ content: string; done: boolean; error?: string }>,
) {
  for (const chunk of chunks) {
    yield chunk;
  }
}

beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

beforeEach(() => {
  vi.clearAllMocks();
  useBuilderStore.getState().reset();
  // 默认: 已创建 Agent、TESTING 状态
  useBuilderStore.setState({ createdAgentId: 42 });
  mockUseAgent.mockReturnValue({
    data: { id: 42, status: 'testing', name: '测试 Agent' },
    isLoading: false,
  });
});

describe('TestSandbox', () => {
  // ── 加载状态 ──

  it('未创建 Agent 时显示加载状态', () => {
    useBuilderStore.setState({ createdAgentId: null });

    render(<TestSandbox token="test-token" />);

    expect(screen.getByText('正在创建测试环境…')).toBeInTheDocument();
  });

  it('Agent 加载中时显示加载状态', () => {
    mockUseAgent.mockReturnValue({ data: undefined, isLoading: true });

    render(<TestSandbox token="test-token" />);

    expect(screen.getByText('正在创建测试环境…')).toBeInTheDocument();
  });

  it('Agent 非 TESTING 状态时显示加载状态', () => {
    mockUseAgent.mockReturnValue({
      data: { id: 42, status: 'active' },
      isLoading: false,
    });

    render(<TestSandbox token="test-token" />);

    expect(screen.getByText('正在创建测试环境…')).toBeInTheDocument();
  });

  // ── 就绪状态 ──

  it('Runtime 就绪后显示沙盒界面', () => {
    render(<TestSandbox token="test-token" />);

    expect(screen.getByText('测试沙盒')).toBeInTheDocument();
    expect(screen.getByText('测试环境已就绪，开始和你的 Agent 对话')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('输入测试消息…')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '发送' })).toBeInTheDocument();
  });

  it('空消息时发送按钮禁用', () => {
    render(<TestSandbox token="test-token" />);

    expect(screen.getByRole('button', { name: '发送' })).toBeDisabled();
  });

  // ── 发送消息 ──

  it('发送消息时创建对话并流式接收响应', async () => {
    const user = userEvent.setup();

    // mock: 创建对话返回 id=100
    mockPost.mockResolvedValue({ data: { id: 100 } });

    // mock: SSE 流式返回
    mockParseSSEStream.mockReturnValue(
      createMockSSEStream([
        { content: '你好', done: false },
        { content: '！我是测试 Agent', done: false },
        { content: '', done: true },
      ]),
    );

    render(<TestSandbox token="test-token" />);

    // 输入并发送消息
    await user.type(screen.getByPlaceholderText('输入测试消息…'), '你好');
    await user.click(screen.getByRole('button', { name: '发送' }));

    // 验证用户消息立即出现
    expect(screen.getByText('你好')).toBeInTheDocument();

    // 验证创建对话 API 调用
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/api/v1/conversations', {
        agent_id: 42,
        title: '测试对话 — Agent #42',
      });
    });

    // 验证 SSE 调用参数
    await waitFor(() => {
      expect(mockParseSSEStream).toHaveBeenCalledWith({
        url: 'http://localhost:8000/api/v1/conversations/100/messages/stream',
        token: 'test-token',
        method: 'POST',
        body: { content: '你好' },
        signal: expect.any(AbortSignal),
      });
    });

    // 流完成后，Agent 响应出现在消息列表
    await waitFor(() => {
      expect(screen.getByText('你好！我是测试 Agent')).toBeInTheDocument();
    });
  });

  it('第二条消息复用已有的对话 ID', async () => {
    const user = userEvent.setup();

    mockPost.mockResolvedValue({ data: { id: 200 } });

    // 第一条消息
    mockParseSSEStream.mockReturnValueOnce(createMockSSEStream([{ content: '回复1', done: true }]));

    render(<TestSandbox token="test-token" />);

    await user.type(screen.getByPlaceholderText('输入测试消息…'), '第一条');
    await user.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      expect(screen.getByText('回复1')).toBeInTheDocument();
    });

    // 第二条消息
    mockParseSSEStream.mockReturnValueOnce(createMockSSEStream([{ content: '回复2', done: true }]));

    await user.type(screen.getByPlaceholderText('输入测试消息…'), '第二条');
    await user.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      expect(screen.getByText('回复2')).toBeInTheDocument();
    });

    // 对话创建 API 只调用了一次（第一条消息时）
    expect(mockPost).toHaveBeenCalledTimes(1);
  });

  // ── 错误处理 ──

  it('SSE 流返回错误时显示错误提示', async () => {
    const user = userEvent.setup();

    mockPost.mockResolvedValue({ data: { id: 300 } });
    mockParseSSEStream.mockReturnValue(
      createMockSSEStream([{ content: '', done: false, error: 'Agent 执行超时' }]),
    );

    render(<TestSandbox token="test-token" />);

    await user.type(screen.getByPlaceholderText('输入测试消息…'), '测试');
    await user.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      expect(screen.getByText('Agent 执行超时')).toBeInTheDocument();
    });
  });

  it('创建对话失败时显示错误提示', async () => {
    const user = userEvent.setup();

    mockPost.mockRejectedValue(new Error('网络错误'));

    render(<TestSandbox token="test-token" />);

    await user.type(screen.getByPlaceholderText('输入测试消息…'), '测试');
    await user.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      expect(screen.getByText('网络错误')).toBeInTheDocument();
    });
  });

  // ── 发送状态 ──

  it('发送中输入框和按钮禁用', async () => {
    const user = userEvent.setup();

    mockPost.mockResolvedValue({ data: { id: 400 } });

    // 返回一个永远不会完成的 generator
    let resolve: (() => void) | undefined;
    const pendingPromise = new Promise<void>((r) => {
      resolve = r;
    });
    mockParseSSEStream.mockReturnValue(
      (async function* () {
        await pendingPromise;
        yield { content: '', done: true };
      })(),
    );

    render(<TestSandbox token="test-token" />);

    await user.type(screen.getByPlaceholderText('输入测试消息…'), '测试');
    await user.click(screen.getByRole('button', { name: '发送' }));

    // 发送中时输入框和按钮禁用
    await waitFor(() => {
      expect(screen.getByPlaceholderText('输入测试消息…')).toBeDisabled();
      expect(screen.getByRole('button', { name: '发送' })).toBeDisabled();
    });

    // 清理：解除挂起以避免测试泄漏
    resolve?.();
  });
});
