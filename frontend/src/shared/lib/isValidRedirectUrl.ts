// URL 白名单验证 — 防止开放重定向攻击 (Open Redirect)
// 仅允许同源路径或 HTTPS 协议的可信域名

import { env } from '@/shared/config/env';

/**
 * 验证重定向 URL 安全性
 * - 同源相对路径 ("/callback") → 允许
 * - 与 API 同域的 HTTPS URL → 允许
 * - 其他 → 拒绝
 */
export function isValidRedirectUrl(url: string): boolean {
  // 允许相对路径（以 / 开头但不是 // 开头，防止协议相对 URL）
  if (url.startsWith('/') && !url.startsWith('//')) {
    return true;
  }

  try {
    const parsed = new URL(url);

    // 仅允许 HTTPS 协议
    if (parsed.protocol !== 'https:') {
      return false;
    }

    // 从 API base URL 提取可信域名
    const apiBase = env.VITE_API_BASE_URL;
    if (apiBase) {
      const apiHost = new URL(apiBase).host;
      // 允许 API 同域或其子域
      if (parsed.host === apiHost || parsed.host.endsWith(`.${apiHost}`)) {
        return true;
      }
    }

    // 允许当前页面同域
    if (parsed.host === window.location.host) {
      return true;
    }

    return false;
  } catch {
    return false;
  }
}
