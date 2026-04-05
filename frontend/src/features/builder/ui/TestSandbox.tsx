// TestSandbox — 测试沙盒面板
// 调用 start-testing API 创建 Runtime，就绪后通过 execution API 提供真实对话
// 使用 shared 层 parseSSEStream + apiClient，避免跨 feature 依赖

import { useState, useRef, useEffect, useCallback } from 'react';

import { useAgent } from '@/features/agents';
import { apiClient } from '@/shared/api';
import { env } from '@/shared/config/env';
import { extractApiError } from '@/shared/lib/extractApiError';
import { parseSSEStream } from '@/shared/lib/parseSSEStream';
import { Button, Spinner } from '@/shared/ui';

import { useBuilderCreatedAgentId } from '../model/store';

// SSE 响应 chunk 类型（与 execution 模块 SSEChunk 结构一致）
interface SSEChunk {
  content: string;
  done: boolean;
  message_id?: number;
  token_count?: number;
  error?: string;
}

// 工具调用引用（预留，后续扩展 SSE chunk 时填充）
interface ToolCallRef {
  tool_name: string;
  status: 'pending' | 'success' | 'error';
}

// 知识库引用（预留，后续扩展 SSE chunk 时填充）
interface KnowledgeRef {
  source: string;
  section?: string;
}

interface TestMessage {
  role: 'user' | 'agent';
  content: string;
  tool_calls?: ToolCallRef[];
  knowledge_refs?: KnowledgeRef[];
}

interface TestSandboxProps {
  /** 认证 token，由页面层从 auth store 获取后传入（避免跨 feature 依赖） */
  token: string | null;
}

export function TestSandbox({ token }: TestSandboxProps) {
  const agentId = useBuilderCreatedAgentId();
  const { data: agent, isLoading: isLoadingAgent } = useAgent(agentId ?? undefined);
  const [testMessages, setTestMessages] = useState<TestMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const conversationIdRef = useRef<number | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [testMessages, streamingContent]);

  // 组件卸载时取消进行中的 SSE 连接
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const isRuntimeReady = agent?.status === 'testing';

  const handleSendMessage = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const text = inputValue.trim();
      if (!text || isSending || !agentId) return;

      // 添加用户消息到列表
      setTestMessages((prev) => [...prev, { role: 'user', content: text }]);
      setInputValue('');
      setIsSending(true);
      setError(null);
      setStreamingContent('');

      // 取消上一次未完成的 SSE 连接
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        // 首次发送时创建对话
        if (conversationIdRef.current === null) {
          const { data } = await apiClient.post<{ id: number }>('/api/v1/conversations', {
            agent_id: agentId,
            title: `测试对话 — Agent #${agentId}`,
          });
          conversationIdRef.current = data.id;
        }

        const conversationId = conversationIdRef.current;
        const url = `${env.VITE_API_BASE_URL}/api/v1/conversations/${conversationId}/messages/stream`;

        let accumulated = '';

        for await (const chunk of parseSSEStream<SSEChunk>({
          url,
          token,
          method: 'POST',
          body: { content: text },
          signal: controller.signal,
        })) {
          if (chunk.error) {
            throw new Error(chunk.error);
          }
          if (chunk.content) {
            accumulated += chunk.content;
            setStreamingContent(accumulated);
          }
          if (chunk.done) {
            break;
          }
        }

        // 流完成 → 将完整响应添加到消息列表
        if (accumulated) {
          setTestMessages((prev) => [...prev, { role: 'agent', content: accumulated }]);
        }
      } catch (err) {
        // 用户主动取消时不显示错误
        if (err instanceof DOMException && err.name === 'AbortError') {
          return;
        }
        setError(extractApiError(err, '发送消息失败，请重试'));
      } finally {
        abortControllerRef.current = null;
        setIsSending(false);
        setStreamingContent('');
      }
    },
    [inputValue, isSending, agentId, token],
  );

  // Runtime 尚未就绪
  if (!agentId || isLoadingAgent || !isRuntimeReady) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center">
        <Spinner />
        <p className="mt-3 text-sm text-gray-600">正在创建测试环境…</p>
        <p className="mt-1 text-xs text-gray-400">
          系统正在为你的 Agent 部署专属 Runtime，这可能需要几秒钟
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* 沙盒头部 */}
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-2 w-2 rounded-full bg-green-500" />
          <span className="text-sm font-medium text-gray-900">测试沙盒</span>
          <span className="text-xs text-gray-500">— Agent #{agentId} 测试环境</span>
        </div>
      </div>

      {/* 测试对话区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {testMessages.length === 0 && !streamingContent && (
          <div className="flex h-full items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-3xl">🧪</p>
              <p className="mt-2 text-sm">测试环境已就绪，开始和你的 Agent 对话</p>
              <p className="mt-1 text-xs">
                你可以模拟真实用户场景，测试 Agent 的回答质量和工具调用
              </p>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {testMessages.map((msg, i) => (
            <TestMessageBubble key={i} message={msg} />
          ))}
        </div>

        {/* 流式输出区域 */}
        {streamingContent && (
          <div className="mt-3">
            <TestMessageBubble message={{ role: 'agent', content: streamingContent }} />
          </div>
        )}

        {isSending && !streamingContent && (
          <div className="mt-3 flex items-center gap-2 text-gray-500">
            <Spinner />
            <span className="text-sm">Agent 正在思考…</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="border-t border-red-100 bg-red-50 px-4 py-2">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* 测试输入区域 */}
      <form onSubmit={(e) => void handleSendMessage(e)} className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isSending}
            placeholder="输入测试消息…"
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500
              disabled:cursor-not-allowed disabled:bg-gray-50"
          />
          <Button type="submit" disabled={isSending || !inputValue.trim()}>
            发送
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── 内部子组件 ──

function TestMessageBubble({ message }: { message: TestMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      <span className="mt-0.5 flex-shrink-0 text-sm" aria-hidden="true">
        {isUser ? '🧑‍💻' : '🤖'}
      </span>
      <div className="max-w-[85%]">
        {/* 消息内容 */}
        <div
          className={`rounded-lg px-3 py-2 ${
            isUser ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-800'
          }`}
        >
          <pre className="whitespace-pre-wrap font-sans text-sm">{message.content}</pre>
        </div>

        {/* Agent 消息: 工具调用可视化 */}
        {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mt-1 space-y-1">
            {message.tool_calls.map((call, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 rounded border border-purple-200 bg-purple-50 px-2 py-1 text-xs"
              >
                <span aria-hidden="true">🔧</span>
                <span className="font-medium text-purple-700">{call.tool_name}</span>
                <span
                  className={`rounded px-1 py-0.5 text-xs ${
                    call.status === 'success'
                      ? 'bg-green-100 text-green-700'
                      : call.status === 'error'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-yellow-100 text-yellow-700'
                  }`}
                >
                  {call.status === 'success' ? '成功' : call.status === 'error' ? '失败' : '调用中'}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Agent 消息: 知识库引用可视化 */}
        {!isUser && message.knowledge_refs && message.knowledge_refs.length > 0 && (
          <div className="mt-1 space-y-1">
            {message.knowledge_refs.map((ref, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 rounded border border-blue-200 bg-blue-50 px-2 py-1 text-xs"
              >
                <span aria-hidden="true">📚</span>
                <span className="text-blue-700">
                  引用: {ref.source}
                  {ref.section && <span className="text-blue-500"> {ref.section}</span>}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
