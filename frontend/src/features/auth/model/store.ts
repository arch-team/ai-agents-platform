// Zustand auth store — Token 持久化到 sessionStorage（标签页级别会话）
// 安全策略: sessionStorage 比 localStorage 安全（标签页隔离，关闭即清除）
// 参考: security.md §3, state-management.md §2.1

import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { useShallow } from 'zustand/shallow';

import { setTokenGetter } from '@/shared/api';

import type { UserSummary } from '@/entities/user';

import type { AuthState } from './types';

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      _hasHydrated: false,
      setAuth: (user: UserSummary, token: string) => {
        // 同步更新 token getter，避免 navigate 后请求无 Bearer header（BUG-7）
        setTokenGetter(() => token);
        set({ user, token, isAuthenticated: true });
      },
      logout: () => {
        setTokenGetter(() => null);
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-session',
      // sessionStorage: 标签页隔离，关闭标签即清除（禁止用 localStorage）
      storage: createJSONStorage(() => sessionStorage),
      // 仅持久化 token — user 信息通过 /auth/me 重新获取
      partialize: (state) => ({ token: state.token }),
      // rehydrate 后恢复 token getter + 标记 hydration 完成
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          setTokenGetter(() => state.token);
        }
        // 无论是否有 token，hydration 完成后标记
        useAuthStore.setState({ _hasHydrated: true });
      },
    },
  ),
);

// 细粒度 selector hooks — useShallow 防止无限重渲染

export const useAuth = () =>
  useAuthStore(
    useShallow((state) => ({
      user: state.user,
      isAuthenticated: state.isAuthenticated,
    })),
  );

export const useAuthToken = () => useAuthStore((state) => state.token);

export const useAuthHasHydrated = () => useAuthStore((state) => state._hasHydrated);

export const useAuthActions = () =>
  useAuthStore(
    useShallow((state) => ({
      setAuth: state.setAuth,
      logout: state.logout,
    })),
  );
