import { Navigate, Outlet } from 'react-router-dom';

import { useAuth, useAuthToken, useAuthHasHydrated, useCurrentUser } from '@/features/auth';
import { Spinner } from '@/shared/ui';

export function ProtectedRoute() {
  const hasHydrated = useAuthHasHydrated();
  const token = useAuthToken();
  const { isAuthenticated } = useAuth();
  const { isLoading } = useCurrentUser();

  // persist rehydration 尚未完成 — 等待 sessionStorage 恢复 token 后再判断
  if (!hasHydrated) {
    return <Spinner fullScreen />;
  }

  // token 存在但用户信息还在加载中，显示加载态而不是重定向到登录页
  if (token && isLoading) {
    return <Spinner fullScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
