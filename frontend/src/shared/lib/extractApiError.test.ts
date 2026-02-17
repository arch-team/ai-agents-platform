import axios, { AxiosError, AxiosHeaders } from 'axios';
import { describe, it, expect } from 'vitest';

import { extractApiError } from './extractApiError';

// 创建模拟 AxiosError 的辅助函数
function createAxiosError(data: Record<string, unknown>, status = 400): AxiosError {
  const error = new AxiosError('Request failed', 'ERR_BAD_REQUEST', undefined, undefined, {
    data,
    status,
    statusText: 'Bad Request',
    headers: {},
    config: { headers: new AxiosHeaders() },
  });
  return error;
}

describe('extractApiError', () => {
  it('应该从 axios 错误的 message 字段提取消息', () => {
    const error = createAxiosError({ message: '用户名已存在' });
    expect(extractApiError(error, '默认错误')).toBe('用户名已存在');
  });

  it('应该从 axios 错误的 detail 字段提取消息', () => {
    const error = createAxiosError({ detail: '认证失败' });
    expect(extractApiError(error, '默认错误')).toBe('认证失败');
  });

  it('应该从 axios 错误的 errors 数组提取消息', () => {
    const error = createAxiosError({ errors: [{ message: '字段验证失败' }] });
    expect(extractApiError(error, '默认错误')).toBe('字段验证失败');
  });

  it('应该优先使用 message 字段', () => {
    const error = createAxiosError({ message: '主消息', detail: '详细消息' });
    expect(extractApiError(error, '默认错误')).toBe('主消息');
  });

  it('应该在 axios 错误无数据时返回默认消息', () => {
    const error = new AxiosError('Request failed');
    expect(extractApiError(error, '默认错误')).toBe('默认错误');
  });

  it('应该从原生 Error 对象提取消息', () => {
    const error = new Error('SSE 流中断');
    expect(extractApiError(error, '默认错误')).toBe('SSE 流中断');
  });

  it('应该对未知类型返回默认消息', () => {
    expect(extractApiError('string error', '默认错误')).toBe('默认错误');
    expect(extractApiError(42, '默认错误')).toBe('默认错误');
    expect(extractApiError(null, '默认错误')).toBe('默认错误');
    expect(extractApiError(undefined, '默认错误')).toBe('默认错误');
  });
});
