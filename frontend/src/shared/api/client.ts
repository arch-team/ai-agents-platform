import axios from 'axios';

import { env } from '@/shared/config/env';

export const apiClient = axios.create({
  baseURL: env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// JWT 拦截器 — 通过注入函数从 auth store 读取 token
// 使用函数引用避免 shared 层直接依赖 features 层
let getToken: (() => string | null) | null = null;

export function setTokenGetter(getter: () => string | null) {
  getToken = getter;
}

apiClient.interceptors.request.use((config) => {
  const token = getToken?.();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 错误拦截器 — 401 自动跳转登录
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);
