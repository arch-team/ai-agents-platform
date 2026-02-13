// Auth 状态类型定义

import type { UserSummary } from '@/entities/user';

export interface AuthState {
  user: UserSummary | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: UserSummary, token: string) => void;
  logout: () => void;
}
