// 认证相关 API queries/mutations

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api';

import { useAuthActions, useAuthToken } from '../model/store';

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
      setAuth(
        {
          id: data.user.id,
          email: data.user.email,
          name: data.user.name,
          role: data.user.role as 'admin' | 'developer' | 'viewer',
          created_at: '',
          updated_at: '',
        },
        data.access_token,
      );
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

  return useQuery({
    queryKey: authKeys.me(),
    queryFn: async () => {
      const { data } = await apiClient.get<LoginResponse['user']>('/api/v1/auth/me');
      // TanStack Query v5 移除了 onSuccess，在 queryFn 内处理副作用
      if (token) {
        setAuth(
          {
            id: data.id,
            email: data.email,
            name: data.name,
            role: data.role as 'admin' | 'developer' | 'viewer',
            created_at: '',
            updated_at: '',
          },
          token,
        );
      }
      return data;
    },
    enabled: !!token,
    retry: false,
  });
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
