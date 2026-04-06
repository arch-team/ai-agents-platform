// 导航守卫 — 防止用户在有未保存工作时意外离开页面
// 注意: 项目使用 BrowserRouter（非 data router），不支持 useBlocker，
// 因此使用 beforeunload + popstate + pushState monkey-patch 三层拦截方案
//
// 拦截场景:
// 1. beforeunload — 浏览器标签关闭、刷新、地址栏输入
// 2. popstate — 浏览器前进/后退按钮
// 3. pushState/replaceState monkey-patch — SPA 内部路由（<Link> 点击）

import { useEffect, useRef } from 'react';

export function useNavigationGuard(shouldBlock: boolean, message?: string) {
  const msg = message ?? '你有未保存的更改，确定要离开吗？';
  const shouldBlockRef = useRef(shouldBlock);

  // 同步 ref（在 effect 中更新，避免 render 阶段赋值）
  useEffect(() => {
    shouldBlockRef.current = shouldBlock;
  }, [shouldBlock]);

  // 拦截浏览器级导航（标签关闭、刷新）
  useEffect(() => {
    if (!shouldBlock) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [shouldBlock]);

  // 拦截浏览器后退/前进按钮
  useEffect(() => {
    if (!shouldBlock) return;

    window.history.pushState({ navigationGuard: true }, '');

    const handlePopState = () => {
      if (shouldBlockRef.current) {
        const confirmed = window.confirm(msg);
        if (!confirmed) {
          window.history.pushState({ navigationGuard: true }, '');
        }
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [shouldBlock, msg]);

  // 拦截 SPA 内部路由导航（React Router <Link> 使用 pushState/replaceState）
  useEffect(() => {
    if (!shouldBlock) return;

    const currentPath = window.location.pathname;
    const originalPushState = window.history.pushState.bind(window.history);
    const originalReplaceState = window.history.replaceState.bind(window.history);

    const interceptNavigation = (
      original: typeof window.history.pushState,
      data: unknown,
      unused: string,
      url?: string | URL | null,
    ): void => {
      // 仅拦截路径变化（忽略同页面 state 更新，如哨兵 pushState）
      const targetPath = url != null ? new URL(String(url), window.location.origin).pathname : null;

      if (targetPath && targetPath !== currentPath) {
        const confirmed = window.confirm(msg);
        if (!confirmed) return;
      }
      original(data, unused, url);
    };

    window.history.pushState = (data, unused, url) =>
      interceptNavigation(originalPushState, data, unused, url);
    window.history.replaceState = (data, unused, url) =>
      interceptNavigation(originalReplaceState, data, unused, url);

    return () => {
      window.history.pushState = originalPushState;
      window.history.replaceState = originalReplaceState;
    };
  }, [shouldBlock, msg]);
}
