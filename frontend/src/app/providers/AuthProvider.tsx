// AuthProvider — 401 事件监听 + 去抖防止循环登出
// Token 注入已移至 auth store 的 setAuth/logout 中同步执行（BUG-7）
// useCurrentUser 由 ProtectedRoute 调用，此处不再重复（BUG-6）

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { UNAUTHORIZED_EVENT } from '@/shared/api';
import { useLogout } from '@/features/auth';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const logout = useLogout();

  // 监听 401 未认证事件，去抖防止循环登出（BUG-6）
  useEffect(() => {
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    const handleUnauthorized = () => {
      if (debounceTimer) return;
      debounceTimer = setTimeout(() => {
        debounceTimer = null;
      }, 1000);
      logout();
      navigate('/login', { replace: true });
    };

    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => {
      window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
      if (debounceTimer) clearTimeout(debounceTimer);
    };
  }, [logout, navigate]);

  return <>{children}</>;
}
