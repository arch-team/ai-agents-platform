// AuthProvider — 桥接 Zustand auth store 与 API client token 注入 + 401 事件监听

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { setTokenGetter, UNAUTHORIZED_EVENT } from '@/shared/api';
import { useAuthToken, useLogout } from '@/features/auth';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthToken();
  const navigate = useNavigate();
  const logout = useLogout();

  // 将 Zustand store 的 token getter 注入到 API client
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
