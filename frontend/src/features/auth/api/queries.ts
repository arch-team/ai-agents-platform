// 认证相关 API queries/mutations

import { useEffect } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import { useAuthActions, useAuthToken } from '../model/store';

import type { User } from '@/entities/user';

import type { LoginRequest, LoginResponse, RegisterRequest } from './types';

// 将 API 返回的用户信息转为完整 User 对象
function toUser(apiUser: LoginResponse['user']): User {
  return { ...apiUser, created_at: '', updated_at: '' };
}

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
      setAuth(toUser(data.user), data.access_token);
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
export function useCurrentUser() {
  const token = useAuthToken();
  const { setAuth } = useAuthActions();

  const query = useQuery({
    queryKey: authKeys.me(),
    queryFn: async () => {
      const { data } = await apiClient.get<LoginResponse['user']>('/api/v1/auth/me');
      return data;
    },
    enabled: !!token,
    retry: false,
  });

  // 将用户信息同步到 auth store（避免在 queryFn 内执行副作用）
  useEffect(() => {
    if (query.data && token) {
      setAuth(toUser(query.data), token);
    }
  }, [query.data, token, setAuth]);

  return query;
}

// 登出辅助：清除 auth 缓存
export function useLogout() {
  const { logout } = useAuthActions();
  const queryClient = useQueryClient();

  return () => {
    logout();
    queryClient.removeQueries({ queryKey: authKeys.all });
  };
}
