// Builder 左侧面板 — 多轮对话气泡 + SSE 流式展示

import { useRef, useEffect, useState } from 'react';

import { Button, Spinner } from '@/shared/ui';

import type { BuilderPhase, ChatMessage, GeneratedBlueprint } from '../api/types';
import {
  useBuilderBlueprint,
  useBuilderIsGenerating,
  useBuilderStreamContent,
  useBuilderError,
  useBuilderMessages,
  useBuilderPhase,
} from '../model/store';

interface BuilderChatProps {
  onSubmitInitial: (prompt: string) => void;
  onSubmitRefine: (message: string) => void;
  onAbort?: () => void;
}

function getPlaceholder(phase: BuilderPhase, hasMessages: boolean): string {
  if (phase === 'configure' && hasMessages) return '描述需要的调整…';
  return '例如：创建一个能够回答客服问题的 Agent，支持退换货查询和订单跟踪…';
}

function getSubmitLabel(phase: BuilderPhase, isGenerating: boolean): string {
  if (isGenerating) return '生成中…';
  if (phase === 'configure') return '发送调整';
  return '开始生成';
}

export function BuilderChat({ onSubmitInitial, onSubmitRefine, onAbort }: BuilderChatProps) {
  const isGenerating = useBuilderIsGenerating();
  const streamContent = useBuilderStreamContent();
  const error = useBuilderError();
  const messages = useBuilderMessages();
  const phase = useBuilderPhase();
  const blueprint = useBuilderBlueprint();
  const [inputValue, setInputValue] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamContent]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const text = inputValue.trim();
    if (isGenerating || !text) return;

    if (phase === 'configure') {
      onSubmitRefine(text);
    } else {
      onSubmitInitial(text);
    }
    setInputValue('');
  };

  return (
    <div className="flex h-full flex-col">
      {/* 对话区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !streamContent && !isGenerating && (
          <div className="flex h-full items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-3xl">💬</p>
              <p className="mt-2 text-sm">输入需求描述，AI 将帮你构建 Agent 蓝图</p>
            </div>
          </div>
        )}

        {/* 历史消息气泡 */}
        <div className="space-y-3">
          {messages.map((msg, i) => {
            // 在最后一条助手消息后展示 Blueprint 折叠摘要
            const isLastAssistant =
              msg.role === 'assistant' && i === messages.length - 1 && blueprint;
            return (
              <div key={i}>
                <MessageBubble message={msg} />
                {isLastAssistant && (
                  <div className="ml-7 mt-1">
                    <BlueprintCollapsible blueprint={blueprint} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 流式内容（当前正在生成的助手消息） */}
        {isGenerating && streamContent && (
          <div className="mt-3">
            <div className="flex items-start gap-2">
              <span className="mt-0.5 flex-shrink-0 text-sm" aria-hidden="true">
                🤖
              </span>
              <div className="min-w-0 rounded-lg bg-gray-100 px-3 py-2">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700">
                  {streamContent}
                </pre>
                <span className="inline-block h-3 w-1 animate-pulse bg-blue-500" />
              </div>
            </div>
          </div>
        )}

        {/* 加载指示器 */}
        {isGenerating && !streamContent && (
          <div className="mt-3 flex items-center gap-2 text-blue-600">
            <Spinner />
            <span className="text-sm">正在生成…</span>
          </div>
        )}

        {/* 错误提示 */}
        {error && (
          <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
            <p role="alert" className="text-sm text-red-600">
              {error}
            </p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            rows={2}
            disabled={isGenerating}
            placeholder={getPlaceholder(phase, messages.length > 0)}
            className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500
              disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-400"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                inputRef.current?.form?.requestSubmit();
              }
            }}
          />
          <div className="flex flex-col gap-1">
            <Button type="submit" disabled={isGenerating || !inputValue.trim()} className="h-full">
              {getSubmitLabel(phase, isGenerating)}
            </Button>
            {isGenerating && onAbort && (
              <Button type="button" variant="outline" onClick={onAbort} className="text-xs">
                取消
              </Button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}

// ── 内部子组件 ──

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      <span className="mt-0.5 flex-shrink-0 text-sm" aria-hidden="true">
        {isUser ? '👤' : '🤖'}
      </span>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 ${
          isUser ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-800'
        }`}
      >
        <pre className="whitespace-pre-wrap font-sans text-sm">{message.content}</pre>
      </div>
    </div>
  );
}

function BlueprintCollapsible({ blueprint }: { blueprint: GeneratedBlueprint }) {
  const [expanded, setExpanded] = useState(false);

  const skillCount = blueprint.skills.length;
  const toolCount = blueprint.tool_bindings.length;
  const roleName = blueprint.persona?.role ?? '未定义';

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50">
      <button
        type="button"
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span className="font-medium text-blue-700">
          📋 蓝图摘要: {roleName} · {skillCount} 技能 · {toolCount} 工具
        </span>
        <span
          className="text-blue-400 transition-transform"
          aria-hidden="true"
          style={{ transform: expanded ? 'rotate(180deg)' : undefined }}
        >
          ▾
        </span>
      </button>

      {expanded && (
        <div className="border-t border-blue-200 px-3 py-2 text-xs text-blue-800">
          {blueprint.persona && (
            <p>
              <span className="font-medium">角色:</span> {blueprint.persona.role} —{' '}
              {blueprint.persona.background}
            </p>
          )}
          {skillCount > 0 && (
            <p className="mt-1">
              <span className="font-medium">技能:</span>{' '}
              {blueprint.skills.map((s) => s.name).join('、')}
            </p>
          )}
          {toolCount > 0 && (
            <p className="mt-1">
              <span className="font-medium">工具:</span>{' '}
              {blueprint.tool_bindings.map((t) => t.display_name).join('、')}
            </p>
          )}
          {blueprint.guardrails.length > 0 && (
            <p className="mt-1">
              <span className="font-medium">护栏:</span> {blueprint.guardrails.length} 条规则
            </p>
          )}
          <p className="mt-1.5 text-blue-500">详细蓝图请查看右侧预览面板 →</p>
        </div>
      )}
    </div>
  );
}
