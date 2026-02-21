// 从 API 错误响应中提取错误消息

import axios from 'axios';

interface ApiErrorData {
  message?: string;
  detail?: string | Array<{ msg?: string; type?: string; loc?: unknown[]; input?: unknown }>;
  errors?: { message?: string }[];
}

/**
 * 从 axios 错误对象中提取可读的错误消息
 * 兼容多种后端错误格式：message / detail (string | FastAPI 422 array) / errors[0].message
 * 同时支持原生 Error 对象（如 SSE 流中抛出的错误）
 * @param error - 错误对象（通常来自 mutation onError 或 SSE 流）
 * @param defaultMessage - 默认错误消息
 */
export function extractApiError(error: unknown, defaultMessage: string): string {
  if (axios.isAxiosError<ApiErrorData>(error)) {
    const data = error.response?.data;
    if (data?.message) return data.message;
    // 处理 FastAPI 422 验证错误 — detail 可能是 string 或 Array<{msg, type, loc, input}>
    if (data?.detail) {
      if (typeof data.detail === 'string') return data.detail;
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        const messages = data.detail
          .map((d) => {
            const field = Array.isArray(d.loc) ? String(d.loc[d.loc.length - 1]) : '';
            return field && d.msg ? `${field}: ${d.msg}` : d.msg || '';
          })
          .filter(Boolean);
        return messages.length > 0 ? messages.join('; ') : defaultMessage;
      }
    }
    return data?.errors?.[0]?.message || defaultMessage;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return defaultMessage;
}
