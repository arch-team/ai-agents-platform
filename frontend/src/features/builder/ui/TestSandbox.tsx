// TestSandbox — 测试沙盒面板
// 调用 start-testing API 创建 Runtime，就绪后提供真实对话界面
// 展示工具调用和知识库引用的可视化反馈

import { useState, useRef, useEffect } from 'react';

import { useAgent } from '@/features/agents';
import { Button, Spinner } from '@/shared/ui';

import { useBuilderCreatedAgentId } from '../model/store';

// 工具调用引用
interface ToolCallRef {
  tool_name: string;
  status: 'pending' | 'success' | 'error';
}

// 知识库引用
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

export function TestSandbox() {
  const agentId = useBuilderCreatedAgentId();
  const { data: agent, isLoading: isLoadingAgent } = useAgent(agentId ?? undefined);
  const [testMessages, setTestMessages] = useState<TestMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [testMessages]);

  const isRuntimeReady = agent?.status === 'testing';

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

  const handleSendMessage = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const text = inputValue.trim();
    if (!text || isSending) return;

    const userMsg: TestMessage = { role: 'user', content: text };
    setTestMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsSending(true);

    // TODO: 对接 execution 模块的实际对话 API (路由到 TESTING Runtime)
    // 当前使用占位响应演示工具调用和知识库引用的可视化格式
    setTimeout(() => {
      setTestMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          content: `[测试环境] Agent Runtime 已就绪 (Agent #${agentId})。实际对话功能将在 execution 模块集成后启用。`,
          tool_calls: [{ tool_name: '订单查询 API', status: 'success' }],
          knowledge_refs: [{ source: '退换货政策', section: '§3.2 退货流程' }],
        },
      ]);
      setIsSending(false);
    }, 1000);
  };

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
        {testMessages.length === 0 && (
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

        {isSending && (
          <div className="mt-3 flex items-center gap-2 text-gray-500">
            <Spinner />
            <span className="text-sm">Agent 正在思考…</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

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
