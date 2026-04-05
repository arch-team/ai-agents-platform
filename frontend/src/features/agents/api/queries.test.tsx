// Agent query keys + lifecycle mutations 测试

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';

import { server } from '../../../../tests/mocks/server';

import { agentKeys, useStartTesting, useGoLive, useTakeOffline } from './queries';

const API_BASE = 'http://localhost:8000';

// Mock Agent 数据工厂
function makeAgent(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    name: '测试 Agent',
    description: '',
    system_prompt: '',
    status: 'draft',
    owner_id: 1,
    config: {
      model_id: 'claude-sonnet-4-6',
      temperature: 0.7,
      max_tokens: 2048,
      top_p: 1,
      enable_memory: false,
    },
    tool_ids: [],
    created_at: '2026-04-05T00:00:00Z',
    updated_at: '2026-04-05T00:00:00Z',
    ...overrides,
  };
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return { wrapper, queryClient };
}

describe('agentKeys', () => {
  it('should generate correct key shapes', () => {
    expect(agentKeys.all).toEqual(['agents']);
    expect(agentKeys.lists()).toEqual(['agents', 'list']);
    expect(agentKeys.detail(42)).toEqual(['agents', 'detail', 42]);
  });
});

describe('lifecycle mutations', () => {
  it('useStartTesting should call POST /agents/:id/start-testing and return testing agent', async () => {
    const testingAgent = makeAgent({ status: 'testing' });
    server.use(
      http.post(`${API_BASE}/api/v1/agents/1/start-testing`, () => HttpResponse.json(testingAgent)),
    );

    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useStartTesting(), { wrapper });

    await act(() => result.current.mutateAsync(1));

    await waitFor(() => expect(result.current.data).toMatchObject({ id: 1, status: 'testing' }));
    expect(queryClient.getQueryData(agentKeys.detail(1))).toMatchObject({ status: 'testing' });
  });

  it('useGoLive should call POST /agents/:id/go-live and return active agent', async () => {
    const activeAgent = makeAgent({ status: 'active' });
    server.use(
      http.post(`${API_BASE}/api/v1/agents/1/go-live`, () => HttpResponse.json(activeAgent)),
    );

    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useGoLive(), { wrapper });

    await act(() => result.current.mutateAsync(1));

    await waitFor(() => expect(result.current.data).toMatchObject({ id: 1, status: 'active' }));
    expect(queryClient.getQueryData(agentKeys.detail(1))).toMatchObject({ status: 'active' });
  });

  it('useTakeOffline should call POST /agents/:id/take-offline and return archived agent', async () => {
    const archivedAgent = makeAgent({ status: 'archived' });
    server.use(
      http.post(`${API_BASE}/api/v1/agents/1/take-offline`, () => HttpResponse.json(archivedAgent)),
    );

    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useTakeOffline(), { wrapper });

    await act(() => result.current.mutateAsync(1));

    await waitFor(() => expect(result.current.data).toMatchObject({ id: 1, status: 'archived' }));
    expect(queryClient.getQueryData(agentKeys.detail(1))).toMatchObject({ status: 'archived' });
  });
});
