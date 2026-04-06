// AuthProvider — 桥接 Zustand auth store 与 API client token 注入 + 401 事件监听
// + 页面加载时通过 httpOnly Cookie 自动恢复会话

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { setTokenGetter, UNAUTHORIZED_EVENT } from '@/shared/api';
import { useAuthToken, useCurrentUser, useLogout } from '@/features/auth';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthToken();
  const navigate = useNavigate();
  const logout = useLogout();

  // 页面加载时自动尝试 /auth/me 恢复会话（httpOnly Cookie 自动携带）
  useCurrentUser();

  // 将 Zustand store 的 token getter 注入到 API client（Bearer header 仍作为 Cookie 的补充）
  useEffect(() => {
    setTokenGetter(() => token);
  }, [token]);

  // 监听 401 未认证事件，通过 React Router 导航到登录页（保持 SPA 体验）
  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
      navigate('/login', { replace: true });
    };

    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, [logout, navigate]);

  return <>{children}</>;
}
