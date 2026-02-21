import { AxiosError, AxiosHeaders } from 'axios';
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

  it('应该从 FastAPI 422 验证错误的 detail 数组提取消息', () => {
    const error = createAxiosError(
      {
        detail: [
          { type: 'string_too_short', loc: ['body', 'name'], msg: '最少 1 个字符', input: '' },
        ],
      },
      422,
    );
    expect(extractApiError(error, '默认错误')).toBe('name: 最少 1 个字符');
  });

  it('应该拼接多个 FastAPI 422 验证错误', () => {
    const error = createAxiosError(
      {
        detail: [
          { type: 'string_too_short', loc: ['body', 'name'], msg: '最少 1 个字符', input: '' },
          { type: 'missing', loc: ['body', 'system_prompt'], msg: '字段必填', input: null },
        ],
      },
      422,
    );
    expect(extractApiError(error, '默认错误')).toBe('name: 最少 1 个字符; system_prompt: 字段必填');
  });

  it('应该处理 detail 数组中无 loc 的情况', () => {
    const error = createAxiosError({ detail: [{ msg: '请求无效' }] }, 422);
    expect(extractApiError(error, '默认错误')).toBe('请求无效');
  });

  it('应该处理空 detail 数组返回默认消息', () => {
    const error = createAxiosError({ detail: [] }, 422);
    expect(extractApiError(error, '默认错误')).toBe('默认错误');
  });
});
