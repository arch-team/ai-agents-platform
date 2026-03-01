import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import type { PageResponse } from '@/shared/types';

import { server } from '../../../../tests/mocks/server';

import type { Conversation } from '../api/types';

import { ConversationList } from './ConversationList';

const API_BASE = 'http://localhost:8000';

// 测试数据
const mockConversations: Conversation[] = [
  {
    id: 1,
    title: '关于 AI 的讨论',
    agent_id: 1,
    user_id: 1,
    status: 'active',
    message_count: 5,
    total_tokens: 200,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-15T10:30:00Z',
  },
  {
    id: 2,
    title: '',
    agent_id: 1,
    user_id: 1,
    status: 'completed',
    message_count: 10,
    total_tokens: 500,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-16T08:00:00Z',
  },
];

const mockResponse: PageResponse<Conversation> = {
  items: mockConversations,
  total: 2,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('ConversationList', () => {
  const defaultProps = {
    selectedId: null,
    onSelect: vi.fn(),
    onNewConversation: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    server.use(http.get(`${API_BASE}/api/v1/conversations`, () => HttpResponse.json(mockResponse)));
  });

  it('应显示加载状态', () => {
    render(<ConversationList {...defaultProps} />, { wrapper: createWrapper() });

    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应显示对话列表', async () => {
    render(<ConversationList {...defaultProps} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('关于 AI 的讨论')).toBeInTheDocument();
    });
    expect(screen.getByText('5 条消息')).toBeInTheDocument();
  });

  it('无标题时应显示默认对话标题', async () => {
    render(<ConversationList {...defaultProps} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('对话 #2')).toBeInTheDocument();
    });
  });

  it('应显示空状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/conversations`, () =>
        HttpResponse.json({
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          total_pages: 0,
        }),
      ),
    );

    render(<ConversationList {...defaultProps} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('暂无对话')).toBeInTheDocument();
    });
  });

  it('应显示错误状态', async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/conversations`, () =>
        HttpResponse.json({ message: '服务器错误' }, { status: 500 }),
      ),
    );

    render(<ConversationList {...defaultProps} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('点击对话项应调用 onSelect', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();

    render(<ConversationList {...defaultProps} onSelect={handleSelect} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByText('关于 AI 的讨论')).toBeInTheDocument();
    });

    await user.click(screen.getByText('关于 AI 的讨论'));
    expect(handleSelect).toHaveBeenCalledWith(1);
  });

  it('选中的对话应具有 aria-current 属性', async () => {
    render(<ConversationList {...defaultProps} selectedId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('关于 AI 的讨论')).toBeInTheDocument();
    });

    // 找到包含标题的按钮
    const selectedButton = screen.getByText('关于 AI 的讨论').closest('button');
    expect(selectedButton).toHaveAttribute('aria-current', 'true');
  });

  it('未选中的对话不应具有 aria-current 属性', async () => {
    render(<ConversationList {...defaultProps} selectedId={1} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('对话 #2')).toBeInTheDocument();
    });

    const unselectedButton = screen.getByText('对话 #2').closest('button');
    expect(unselectedButton).not.toHaveAttribute('aria-current');
  });

  it('点击新建对话按钮应调用 onNewConversation', async () => {
    const user = userEvent.setup();
    const handleNew = vi.fn();

    render(<ConversationList {...defaultProps} onNewConversation={handleNew} />, {
      wrapper: createWrapper(),
    });

    await user.click(screen.getByRole('button', { name: '新建对话' }));
    expect(handleNew).toHaveBeenCalledTimes(1);
  });

  it('应具有正确的无障碍标签', async () => {
    render(<ConversationList {...defaultProps} />, { wrapper: createWrapper() });

    // 侧边栏应有 aria-label
    expect(screen.getByRole('complementary', { name: '对话列表' })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('关于 AI 的讨论')).toBeInTheDocument();
    });

    // 导航区域应有 aria-label
    expect(screen.getByRole('navigation', { name: '对话历史' })).toBeInTheDocument();
  });

  it('应传递 agentId 参数进行过滤', async () => {
    let capturedUrl: URL | undefined;
    server.use(
      http.get(`${API_BASE}/api/v1/conversations`, ({ request }) => {
        capturedUrl = new URL(request.url);
        return HttpResponse.json(mockResponse);
      }),
    );

    render(<ConversationList {...defaultProps} agentId={42} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('关于 AI 的讨论')).toBeInTheDocument();
    });

    expect(capturedUrl?.searchParams.get('agent_id')).toBe('42');
  });
});
