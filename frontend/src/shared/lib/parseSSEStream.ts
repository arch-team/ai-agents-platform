// SSE 流解析器 — 通用 fetch + ReadableStream 封装
// 从 features/execution 和 features/team-executions 中提取的公共逻辑
// 原生 EventSource 不支持自定义 header，因此用 fetch 实现

export interface SSERequestConfig {
  /** 请求 URL */
  url: string;
  /** 认证 token */
  token: string | null;
  /** HTTP 方法（默认 GET） */
  method?: 'GET' | 'POST';
  /** POST 请求体（仅 method 为 POST 时使用） */
  body?: object;
}

/**
 * 通用 SSE 流解析生成器
 * 支持 GET 和 POST 两种模式，通过泛型参数指定 chunk 类型
 */
export async function* parseSSEStream<T>(config: SSERequestConfig): AsyncGenerator<T> {
  const { url, token, method = 'GET', body } = config;

  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  if (method === 'POST') {
    headers['Content-Type'] = 'application/json';
  } else {
    headers['Accept'] = 'text/event-stream';
  }

  const response = await fetch(url, {
    method,
    headers,
    ...(method === 'POST' && body ? { body: JSON.stringify(body) } : {}),
  });

  if (!response.ok) {
    throw new Error(`SSE 请求失败: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('无法读取响应流');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data) {
            try {
              yield JSON.parse(data) as T;
            } catch {
              // 忽略解析失败的行
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
