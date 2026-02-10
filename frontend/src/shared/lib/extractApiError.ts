// 从 API 错误响应中提取错误消息

import axios from 'axios';

/**
 * 从 axios 错误对象中提取可读的错误消息
 * @param error - 错误对象（通常来自 mutation onError）
 * @param defaultMessage - 默认错误消息
 */
export function extractApiError(error: unknown, defaultMessage: string): string {
  if (axios.isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message || defaultMessage;
  }
  return defaultMessage;
}
