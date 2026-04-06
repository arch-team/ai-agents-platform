// 导航守卫 — 防止用户在有未保存工作时意外离开页面（BUG-4）

import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';

export function useNavigationGuard(shouldBlock: boolean, message?: string) {
  const msg = message ?? '你有未保存的更改，确定要离开吗？';

  // 拦截 SPA 内导航（React Router）
  const blocker = useBlocker(shouldBlock);

  useEffect(() => {
    if (blocker.state === 'blocked') {
      const confirmed = window.confirm(msg);
      if (confirmed) {
        blocker.proceed();
      } else {
        blocker.reset();
      }
    }
  }, [blocker, msg]);

  // 拦截浏览器级导航（标签关闭、刷新、外部链接）
  useEffect(() => {
    if (!shouldBlock) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [shouldBlock]);
}
