import { describe, it, expect, vi, beforeEach } from 'vitest';

// mock env 模块，使测试不依赖真实环境变量
vi.mock('@/shared/config/env', () => ({
  env: { VITE_API_BASE_URL: 'https://api.example.com' },
}));

import { isValidRedirectUrl } from './isValidRedirectUrl';

describe('isValidRedirectUrl', () => {
  beforeEach(() => {
    // 模拟当前页面 host
    Object.defineProperty(window, 'location', {
      value: { host: 'app.example.com' },
      writable: true,
    });
  });

  it('应允许相对路径', () => {
    expect(isValidRedirectUrl('/callback')).toBe(true);
    expect(isValidRedirectUrl('/auth/sso/callback?code=abc')).toBe(true);
  });

  it('应拒绝协议相对 URL (//)', () => {
    expect(isValidRedirectUrl('//evil.com/attack')).toBe(false);
  });

  it('应允许 API 同域的 HTTPS URL', () => {
    expect(isValidRedirectUrl('https://api.example.com/auth/callback')).toBe(true);
  });

  it('应允许 API 子域的 HTTPS URL', () => {
    expect(isValidRedirectUrl('https://sso.api.example.com/callback')).toBe(true);
  });

  it('应允许当前页面同域', () => {
    expect(isValidRedirectUrl('https://app.example.com/dashboard')).toBe(true);
  });

  it('应拒绝不可信的外部域名', () => {
    expect(isValidRedirectUrl('https://evil.com/phishing')).toBe(false);
  });

  it('应拒绝 HTTP 协议', () => {
    expect(isValidRedirectUrl('http://api.example.com/callback')).toBe(false);
  });

  it('应拒绝 javascript: 协议', () => {
    expect(isValidRedirectUrl('javascript:alert(1)')).toBe(false);
  });

  it('应拒绝无效 URL', () => {
    expect(isValidRedirectUrl('')).toBe(false);
    expect(isValidRedirectUrl('not-a-url')).toBe(false);
  });
});
