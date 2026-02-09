// AuthProvider — 桥接 Zustand auth store 与 API client token 注入

import { useEffect } from 'react';

import { setTokenGetter } from '@/shared/api';
import { useAuthToken } from '@/features/auth';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthToken();

  // 将 Zustand store 的 token getter 注入到 API client
  useEffect(() => {
    setTokenGetter(() => token);
  }, [token]);

  return <>{children}</>;
}
