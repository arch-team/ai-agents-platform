// Zustand auth store — Token 仅存内存，刷新页面后需重新认证

import { create } from 'zustand';
import { useShallow } from 'zustand/shallow';

import { setTokenGetter } from '@/shared/api';

import type { UserSummary } from '@/entities/user';

import type { AuthState } from './types';

const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  setAuth: (user: UserSummary, token: string) => {
    // 同步更新 token getter，避免 navigate 后请求无 Bearer header（BUG-7）
    setTokenGetter(() => token);
    set({ user, token, isAuthenticated: true });
  },
  logout: () => {
    setTokenGetter(() => null);
    set({ user: null, token: null, isAuthenticated: false });
  },
}));

// 细粒度 selector hooks — useShallow 防止无限重渲染

export const useAuth = () =>
  useAuthStore(
    useShallow((state) => ({
      user: state.user,
      isAuthenticated: state.isAuthenticated,
    })),
  );

export const useAuthToken = () => useAuthStore((state) => state.token);

export const useAuthActions = () =>
  useAuthStore(
    useShallow((state) => ({
      setAuth: state.setAuth,
      logout: state.logout,
    })),
  );
