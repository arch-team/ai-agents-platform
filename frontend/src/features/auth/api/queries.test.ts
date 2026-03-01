// auth API hooks 单元测试
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { createElement } from 'react';

import { server } from '../../../../tests/mocks/server';

import { useAuthActions } from '../model/store';

import { useLogin, useRegister, useCurrentUser, useLogout, authKeys } from './queries';

const API_BASE = 'http://localhost:8000';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return {
    queryClient,
    Wrapper: ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children),
  };
}

// 重置 auth store 避免跨测试污染（useLogin onSuccess 会设置 token）
function resetAuthStore() {
  const { result } = renderHook(() => useAuthActions());
  act(() => {
    result.current.logout();
  });
}

describe('auth API hooks', () => {
  beforeEach(() => {
    resetAuthStore();
  });

  describe('useLogin', () => {
    it('登录成功时应返回 token 和用户信息', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useLogin(), { wrapper: Wrapper });

      await act(async () => {
        result.current.mutate({ email: 'test@example.com', password: 'Password1' });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual({
        access_token: 'fake-jwt-token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com', name: '测试用户', role: 'admin' },
      });
    });

    it('登录失败时应返回错误', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useLogin(), { wrapper: Wrapper });

      await act(async () => {
        result.current.mutate({ email: 'wrong@example.com', password: 'wrong' });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useRegister', () => {
    it('注册成功时应返回成功消息', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useRegister(), { wrapper: Wrapper });

      await act(async () => {
        result.current.mutate({
          email: 'new@example.com',
          password: 'Password1',
          name: '新用户',
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual({ message: '注册成功' });
    });

    it('邮箱已存在时应返回错误', async () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useRegister(), { wrapper: Wrapper });

      await act(async () => {
        result.current.mutate({
          email: 'existing@example.com',
          password: 'Password1',
          name: '已存在用户',
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useCurrentUser', () => {
    it('无 token 时不应发起请求', () => {
      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useCurrentUser(), { wrapper: Wrapper });

      expect(result.current.fetchStatus).toBe('idle');
    });

    it('有 token 时应发起请求并返回用户信息', async () => {
      // 先设置 token 到 auth store
      const { result: actionsResult } = renderHook(() => useAuthActions());
      act(() => {
        actionsResult.current.setAuth(
          { id: 1, email: 'test@example.com', name: '测试用户', role: 'admin' },
          'fake-token',
        );
      });

      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useCurrentUser(), { wrapper: Wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual({
        id: 1,
        email: 'test@example.com',
        name: '测试用户',
        role: 'admin',
      });
    });

    it('API 错误时应返回错误状态', async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/auth/me`, () =>
          HttpResponse.json({ message: '未认证' }, { status: 401 }),
        ),
      );

      // 设置 token 以触发请求
      const { result: actionsResult } = renderHook(() => useAuthActions());
      act(() => {
        actionsResult.current.setAuth(
          { id: 1, email: 'test@example.com', name: '测试用户', role: 'admin' },
          'invalid-token',
        );
      });

      const { Wrapper } = createWrapper();
      const { result } = renderHook(() => useCurrentUser(), { wrapper: Wrapper });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useLogout', () => {
    it('登出后应清除 auth 相关的查询缓存', async () => {
      const { queryClient, Wrapper } = createWrapper();

      // 先在缓存中放入 auth 数据
      queryClient.setQueryData(authKeys.me(), {
        id: 1,
        email: 'test@example.com',
        name: '测试用户',
        role: 'admin',
      });

      expect(queryClient.getQueryData(authKeys.me())).toBeTruthy();

      const { result } = renderHook(() => useLogout(), { wrapper: Wrapper });

      act(() => {
        result.current();
      });

      // 缓存应被清除
      expect(queryClient.getQueryData(authKeys.me())).toBeUndefined();
    });
  });
});
