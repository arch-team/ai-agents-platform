// 导航守卫 — 防止用户在有未保存工作时意外离开页面（BUG-4）
// 注意: 项目使用 BrowserRouter（非 data router），不支持 useBlocker，
// 因此使用 beforeunload + pushState 拦截方案

import { useEffect, useRef } from 'react';

export function useNavigationGuard(shouldBlock: boolean, message?: string) {
  const msg = message ?? '你有未保存的更改，确定要离开吗？';
  const shouldBlockRef = useRef(shouldBlock);
  shouldBlockRef.current = shouldBlock;

  // 拦截浏览器级导航（标签关闭、刷新、外部链接、前进/后退）
  useEffect(() => {
    if (!shouldBlock) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };

    // 拦截浏览器后退/前进按钮
    // 先 push 一个哨兵 state，当用户点后退时触发 popstate
    window.history.pushState({ navigationGuard: true }, '');

    const handlePopState = () => {
      if (shouldBlockRef.current) {
        const confirmed = window.confirm(msg);
        if (!confirmed) {
          // 用户取消 — 重新 push 哨兵 state 保持当前页面
          window.history.pushState({ navigationGuard: true }, '');
        }
        // 用户确认 — 允许导航（浏览器已执行后退）
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [shouldBlock, msg]);
}
