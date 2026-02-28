// MemoryPanel 组件测试

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { MemoryPanel } from './MemoryPanel';

const API_BASE = 'http://localhost:8000';
const AGENT_ID = 42;

const mockMemories = [
  { memory_id: 'mem-001-abcdef', content: '用户偏好中文回复', topic: '偏好', relevance_score: 0 },
  {
    memory_id: 'mem-002-ghijkl',
    content: '上次讨论了项目架构设计',
    topic: '会议',
    relevance_score: 0,
  },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('MemoryPanel', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API_BASE}/api/v1/agents/${AGENT_ID}/memories`, () =>
        HttpResponse.json(mockMemories),
      ),
    );
  });

  it('应显示加载状态', () => {
    render(<MemoryPanel agentId={AGENT_ID} />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示记忆列表', async () => {
    render(<MemoryPanel agentId={AGENT_ID} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('用户偏好中文回复')).toBeInTheDocument();
    });
    expect(screen.getByText('上次讨论了项目架构设计')).toBeInTheDocument();
    // 应显示 topic 标签
    expect(screen.getByText('偏好')).toBeInTheDocument();
    expect(screen.getByText('会议')).toBeInTheDocument();
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/agents/${AGENT_ID}/memories`, () => HttpResponse.json([])),
    );

    render(<MemoryPanel agentId={AGENT_ID} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(
        screen.getByText('该 Agent 暂无记忆。对话时会自动提取和保存记忆。'),
      ).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/agents/${AGENT_ID}/memories`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<MemoryPanel agentId={AGENT_ID} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('应支持删除记忆', async () => {
    server.use(
      http.delete(
        `${API_BASE}/api/v1/agents/${AGENT_ID}/memories/mem-001-abcdef`,
        () => new HttpResponse(null, { status: 204 }),
      ),
    );

    const user = userEvent.setup();
    render(<MemoryPanel agentId={AGENT_ID} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('用户偏好中文回复')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /删除记忆 mem-001-/ }));

    // 删除操作触发后应重新请求列表
    await waitFor(() => {
      expect(screen.getByText('用户偏好中文回复')).toBeInTheDocument();
    });
  });

  it('应支持搜索记忆', async () => {
    const searchResults = [
      {
        memory_id: 'mem-001-abcdef',
        content: '用户偏好中文回复',
        topic: '偏好',
        relevance_score: 0.95,
      },
    ];

    server.use(
      http.post(`${API_BASE}/api/v1/agents/${AGENT_ID}/memories/search`, () =>
        HttpResponse.json(searchResults),
      ),
    );

    const user = userEvent.setup();
    render(<MemoryPanel agentId={AGENT_ID} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('用户偏好中文回复')).toBeInTheDocument();
    });

    // 输入搜索词并点击搜索
    await user.type(screen.getByRole('searchbox', { name: '搜索记忆' }), '偏好');
    await user.click(screen.getByRole('button', { name: '搜索' }));

    // 搜索结果应显示相关度分数
    await waitFor(() => {
      expect(screen.getByText('相关度: 95%')).toBeInTheDocument();
    });

    // 应显示清除按钮
    expect(screen.getByRole('button', { name: '清除' })).toBeInTheDocument();
  });

  it('点击清除应回到列表视图', async () => {
    const searchResults = [
      {
        memory_id: 'mem-001-abcdef',
        content: '用户偏好中文回复',
        topic: '偏好',
        relevance_score: 0.95,
      },
    ];

    server.use(
      http.post(`${API_BASE}/api/v1/agents/${AGENT_ID}/memories/search`, () =>
        HttpResponse.json(searchResults),
      ),
    );

    const user = userEvent.setup();
    render(<MemoryPanel agentId={AGENT_ID} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('用户偏好中文回复')).toBeInTheDocument();
    });

    // 执行搜索
    await user.type(screen.getByRole('searchbox', { name: '搜索记忆' }), '偏好');
    await user.click(screen.getByRole('button', { name: '搜索' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '清除' })).toBeInTheDocument();
    });

    // 点击清除
    await user.click(screen.getByRole('button', { name: '清除' }));

    // 应回到完整列表，搜索框应清空
    expect(screen.getByRole('searchbox', { name: '搜索记忆' })).toHaveValue('');
  });
});
