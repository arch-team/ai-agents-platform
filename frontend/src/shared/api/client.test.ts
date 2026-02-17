import { describe, it, expect, vi, beforeEach } from 'vitest';

import { apiClient, setTokenGetter, UNAUTHORIZED_EVENT } from './client';

describe('apiClient', () => {
  it('应该导出 axios 实例', () => {
    expect(apiClient).toBeDefined();
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
  });
});

describe('setTokenGetter', () => {
  beforeEach(() => {
    // 重置 token getter
    setTokenGetter(() => null);
  });

  it('应该在有 token 时添加 Authorization header', async () => {
    setTokenGetter(() => 'test-token');

    // 通过请求拦截器验证
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- 访问 axios 内部拦截器 handlers 无公开类型
    const config = await (apiClient.interceptors.request as any).handlers[0].fulfilled!({
      headers: { ...apiClient.defaults.headers },
    });

    expect(config.headers.Authorization).toBe('Bearer test-token');
  });

  it('应该在无 token 时不添加 Authorization header', async () => {
    setTokenGetter(() => null);

    // 创建全新的 headers 对象，避免前一个测试的污染
    const freshHeaders: Record<string, string> = { 'Content-Type': 'application/json' };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- 访问 axios 内部拦截器 handlers 无公开类型
    const config = await (apiClient.interceptors.request as any).handlers[0].fulfilled!({
      headers: freshHeaders,
    });

    expect(config.headers.Authorization).toBeUndefined();
  });
});

describe('UNAUTHORIZED_EVENT', () => {
  it('应该导出常量事件名', () => {
    expect(UNAUTHORIZED_EVENT).toBe('auth:unauthorized');
  });
});

describe('401 响应拦截器', () => {
  it('应该在 401 时触发自定义事件', async () => {
    const eventHandler = vi.fn();
    window.addEventListener(UNAUTHORIZED_EVENT, eventHandler);

    // 模拟 401 错误
    const { AxiosError, AxiosHeaders } = await import('axios');
    const error = new AxiosError('Unauthorized', 'ERR_BAD_RESPONSE', undefined, undefined, {
      data: {},
      status: 401,
      statusText: 'Unauthorized',
      headers: {},
      config: { headers: new AxiosHeaders() },
    });

    // 获取响应拦截器的 rejected handler
    const rejectedHandler = apiClient.interceptors.response.handlers[0].rejected!;

    await expect(rejectedHandler(error)).rejects.toThrow();
    expect(eventHandler).toHaveBeenCalled();

    window.removeEventListener(UNAUTHORIZED_EVENT, eventHandler);
  });
});
