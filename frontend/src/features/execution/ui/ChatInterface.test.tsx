import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ChatInterface } from './ChatInterface';

// Mock API queries
vi.mock('../api/queries', () => ({
  useConversation: vi.fn(),
  conversationKeys: {
    all: ['conversations'],
    lists: () => ['conversations', 'list'],
    list: (agentId?: number) => ['conversations', 'list', { agentId }],
    details: () => ['conversations', 'detail'],
    detail: (id: number) => ['conversations', 'detail', id],
  },
}));

// Mock stream hook
vi.mock('../api/stream', () => ({
  useSendMessageStream: () => ({
    sendMessage: vi.fn(),
  }),
}));

// Mock store
vi.mock('../model/store', () => ({
  useStreamingContent: () => '',
  useIsStreaming: () => false,
  useChatError: () => null,
  useChatActions: () => ({
    setCurrentConversation: vi.fn(),
    appendStreamContent: vi.fn(),
    clearStream: vi.fn(),
    setStreaming: vi.fn(),
    setError: vi.fn(),
    clearError: vi.fn(),
  }),
}));

import { useConversation } from '../api/queries';

const mockUseConversation = vi.mocked(useConversation);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // jsdom 不支持 scrollIntoView
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('应该在加载时显示 Spinner', () => {
    mockUseConversation.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useConversation>);

    render(<ChatInterface conversationId={1} token={null} />, { wrapper: createWrapper() });
    expect(screen.getByRole('status', { name: '加载中' })).toBeInTheDocument();
  });

  it('应该在加载失败时显示错误信息', () => {
    mockUseConversation.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('请求失败'),
    } as ReturnType<typeof useConversation>);

    render(<ChatInterface conversationId={1} token={null} />, { wrapper: createWrapper() });
    expect(screen.getByRole('alert')).toHaveTextContent('请求失败');
  });

  it('应该显示对话标题和消息列表', () => {
    mockUseConversation.mockReturnValue({
      data: {
        conversation: {
          id: 1,
          title: '测试对话',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 2,
          total_tokens: 100,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        messages: [
          {
            id: 1,
            conversation_id: 1,
            role: 'user' as const,
            content: '你好',
            token_count: 10,
            created_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            conversation_id: 1,
            role: 'assistant' as const,
            content: '你好！有什么可以帮助你的？',
            token_count: 20,
            created_at: '2024-01-01T00:00:01Z',
          },
        ],
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConversation>);

    render(<ChatInterface conversationId={1} token={null} />, { wrapper: createWrapper() });

    expect(screen.getByText('测试对话')).toBeInTheDocument();
    expect(screen.getByText('你好')).toBeInTheDocument();
    expect(screen.getByText('你好！有什么可以帮助你的？')).toBeInTheDocument();
  });

  it('应该在空对话时显示空状态提示', () => {
    mockUseConversation.mockReturnValue({
      data: {
        conversation: {
          id: 1,
          title: '新对话',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 0,
          total_tokens: 0,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        messages: [],
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConversation>);

    render(<ChatInterface conversationId={1} token={null} />, { wrapper: createWrapper() });
    expect(screen.getByText('开始新的对话吧')).toBeInTheDocument();
  });

  it('应该包含消息输入框', () => {
    mockUseConversation.mockReturnValue({
      data: {
        conversation: {
          id: 1,
          title: '测试对话',
          agent_id: 1,
          user_id: 1,
          status: 'active',
          message_count: 0,
          total_tokens: 0,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        messages: [],
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConversation>);

    render(<ChatInterface conversationId={1} token={null} />, { wrapper: createWrapper() });
    expect(screen.getByLabelText('消息输入')).toBeInTheDocument();
  });

  it('应该在对话已结束时不显示输入框', () => {
    mockUseConversation.mockReturnValue({
      data: {
        conversation: {
          id: 1,
          title: '已结束对话',
          agent_id: 1,
          user_id: 1,
          status: 'completed',
          message_count: 2,
          total_tokens: 100,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        messages: [],
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConversation>);

    render(<ChatInterface conversationId={1} token={null} />, { wrapper: createWrapper() });
    expect(screen.queryByLabelText('消息输入')).not.toBeInTheDocument();
    expect(screen.getByText('对话已结束')).toBeInTheDocument();
  });
});
