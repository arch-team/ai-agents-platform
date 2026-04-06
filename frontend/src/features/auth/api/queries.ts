// 认证相关 API queries/mutations

import { useCallback, useEffect } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import { useAuthActions, useAuthToken } from '../model/store';

import type { UserSummary } from '@/entities/user';

import type { LoginRequest, LoginResponse, RegisterRequest } from './types';

// Query Key Factory
export const authKeys = {
  all: ['auth'] as const,
  me: () => [...authKeys.all, 'me'] as const,
};

// 登录 mutation
export function useLogin() {
  const { setAuth } = useAuthActions();

  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const { data } = await apiClient.post<LoginResponse>('/api/v1/auth/login', credentials);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token);
    },
  });
}

// 注册 mutation
export function useRegister() {
  return useMutation({
    mutationFn: async (payload: RegisterRequest) => {
      const { data } = await apiClient.post<{ message: string }>('/api/v1/auth/register', payload);
      return data;
    },
  });
}

// 获取当前用户信息
// Cookie 模式下无需内存 token 即可请求（httpOnly Cookie 自动携带）
export function useCurrentUser() {
  const token = useAuthToken();
  const { setAuth } = useAuthActions();

  const query = useQuery({
    queryKey: authKeys.me(),
    queryFn: async () => {
      const { data } = await apiClient.get<UserSummary>('/api/v1/auth/me');
      return data;
    },
    retry: false,
  });

  // 将用户信息同步到 auth store
  // Cookie 模式: token 可能为空，用占位值标记已认证（实际 token 在 httpOnly Cookie 中）
  useEffect(() => {
    if (query.data) {
      setAuth(query.data, token ?? 'cookie');
    }
  }, [query.data, token, setAuth]);

  return query;
}

// 登出辅助：清除 auth 缓存
export function useLogout() {
  const { logout } = useAuthActions();
  const queryClient = useQueryClient();

  return useCallback(() => {
    logout();
    queryClient.removeQueries({ queryKey: authKeys.all });
  }, [logout, queryClient]);
}
