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
  /** 可选 AbortSignal，用于取消 SSE 连接 */
  signal?: AbortSignal;
}

/**
 * 从 HTTP 错误响应中提取详细错误信息
 */
async function extractResponseError(response: Response): Promise<string> {
  try {
    const text = await response.text();
    const json = JSON.parse(text) as Record<string, unknown>;
    const detail = json.detail ?? json.message ?? json.error;
    if (typeof detail === 'string') return detail;
  } catch {
    // 响应体非 JSON 或读取失败，使用状态码
  }
  return `HTTP ${response.status} ${response.statusText}`;
}

/**
 * 通用 SSE 流解析生成器
 * 支持 GET 和 POST 两种模式，通过泛型参数指定 chunk 类型
 */
export async function* parseSSEStream<T>(config: SSERequestConfig): AsyncGenerator<T> {
  const { url, token, method = 'GET', body, signal } = config;

  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(method === 'POST'
      ? { 'Content-Type': 'application/json' }
      : { Accept: 'text/event-stream' }),
  };

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      signal,
      ...(method === 'POST' && body ? { body: JSON.stringify(body) } : {}),
    });
  } catch (err) {
    // 区分取消和网络错误
    if (err instanceof DOMException && err.name === 'AbortError') {
      return;
    }
    throw new Error('网络连接失败，请检查网络后重试');
  }

  if (!response.ok) {
    const detail = await extractResponseError(response);
    throw new Error(`SSE 请求失败: ${detail}`);
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
            } catch (e) {
              if (import.meta.env.DEV) {
                console.warn('[SSE] JSON 解析失败:', data, e);
              }
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
