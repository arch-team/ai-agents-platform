// 从 API 错误响应中提取错误消息

import axios from 'axios';

interface ApiErrorData {
  message?: string;
  detail?: string;
  errors?: { message?: string }[];
}

/**
 * 从 axios 错误对象中提取可读的错误消息
 * 兼容多种后端错误格式：message / detail / errors[0].message
 * 同时支持原生 Error 对象（如 SSE 流中抛出的错误）
 * @param error - 错误对象（通常来自 mutation onError 或 SSE 流）
 * @param defaultMessage - 默认错误消息
 */
export function extractApiError(error: unknown, defaultMessage: string): string {
  if (axios.isAxiosError<ApiErrorData>(error)) {
    const data = error.response?.data;
    return data?.message || data?.detail || data?.errors?.[0]?.message || defaultMessage;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return defaultMessage;
}
