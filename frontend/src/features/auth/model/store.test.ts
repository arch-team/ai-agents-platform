// auth store 单元测试
// useAuthStore 未导出，通过公开的 selector hooks (useAuth/useAuthToken/useAuthActions) 间接测试
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';

import { useAuth, useAuthToken, useAuthActions } from './store';

import type { UserSummary } from '@/entities/user';

const mockUser: UserSummary = {
  id: 1,
  email: 'test@example.com',
  name: '测试用户',
  role: 'admin',
};

describe('auth store', () => {
  beforeEach(() => {
    // 通过 actions 重置 store 状态
    const { result } = renderHook(() => useAuthActions());
    act(() => {
      result.current.logout();
    });
  });

  it('初始状态应为未认证', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('初始 token 应为 null', () => {
    const { result } = renderHook(() => useAuthToken());
    expect(result.current).toBeNull();
  });

  it('setAuth 应设置用户信息、token 和认证状态', () => {
    const { result: actionsResult } = renderHook(() => useAuthActions());
    const { result: authResult } = renderHook(() => useAuth());
    const { result: tokenResult } = renderHook(() => useAuthToken());

    act(() => {
      actionsResult.current.setAuth(mockUser, 'test-token');
    });

    expect(authResult.current.user).toEqual(mockUser);
    expect(authResult.current.isAuthenticated).toBe(true);
    expect(tokenResult.current).toBe('test-token');
  });

  it('logout 应清除所有认证状态', () => {
    const { result: actionsResult } = renderHook(() => useAuthActions());
    const { result: authResult } = renderHook(() => useAuth());
    const { result: tokenResult } = renderHook(() => useAuthToken());

    // 先登录
    act(() => {
      actionsResult.current.setAuth(mockUser, 'test-token');
    });

    expect(authResult.current.isAuthenticated).toBe(true);

    // 再登出
    act(() => {
      actionsResult.current.logout();
    });

    expect(authResult.current.user).toBeNull();
    expect(authResult.current.isAuthenticated).toBe(false);
    expect(tokenResult.current).toBeNull();
  });

  it('多次 setAuth 应正确更新状态', () => {
    const { result: actionsResult } = renderHook(() => useAuthActions());
    const { result: authResult } = renderHook(() => useAuth());

    const anotherUser: UserSummary = {
      id: 2,
      email: 'another@example.com',
      name: '另一个用户',
      role: 'developer',
    };

    act(() => {
      actionsResult.current.setAuth(mockUser, 'token-1');
    });

    expect(authResult.current.user?.id).toBe(1);

    act(() => {
      actionsResult.current.setAuth(anotherUser, 'token-2');
    });

    expect(authResult.current.user?.id).toBe(2);
    expect(authResult.current.user?.name).toBe('另一个用户');
  });
});
