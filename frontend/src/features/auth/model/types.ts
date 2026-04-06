// Auth 状态类型定义

import type { UserSummary } from '@/entities/user';

export interface AuthState {
  user: UserSummary | null;
  token: string | null;
  isAuthenticated: boolean;
  /** persist rehydration 完成标记（防止 hydration 前误判为未登录） */
  _hasHydrated: boolean;
  setAuth: (user: UserSummary, token: string) => void;
  logout: () => void;
}
