// Builder 左侧面板 — 提示词输入 + SSE 消息流展示

import { useRef, useEffect } from 'react';

import { Button, Spinner } from '@/shared/ui';

import { useBuilderIsGenerating, useBuilderStreamContent, useBuilderError } from '../model/store';

interface BuilderChatProps {
  /** 是否已有活跃会话（控制输入区的可交互状态） */
  hasSession: boolean;
  /** 提交提示词回调 */
  onSubmit: (prompt: string) => void;
}

export function BuilderChat({ hasSession, onSubmit }: BuilderChatProps) {
  const isGenerating = useBuilderIsGenerating();
  const streamContent = useBuilderStreamContent();
  const error = useBuilderError();

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamEndRef = useRef<HTMLDivElement>(null);

  // 流式内容更新时自动滚动到底部
  useEffect(() => {
    if (streamContent) {
      streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [streamContent]);

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const prompt = textareaRef.current?.value.trim();
    if (!prompt || isGenerating) return;
    onSubmit(prompt);
  };

  return (
    <div className="flex h-full flex-col">
      {/* 提示词输入区 */}
      <form onSubmit={handleFormSubmit} className="border-b border-gray-200 p-4">
        <label htmlFor="builder-prompt" className="mb-2 block text-sm font-medium text-gray-700">
          描述你需要的 Agent
        </label>
        <textarea
          id="builder-prompt"
          ref={textareaRef}
          rows={4}
          disabled={hasSession && isGenerating}
          placeholder="例如：创建一个能够回答客服问题的 Agent，支持多轮对话…"
          className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm
            focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500
            disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-400"
          aria-describedby={error ? 'builder-error' : undefined}
        />
        {error && (
          <p id="builder-error" role="alert" className="mt-1 text-sm text-red-600">
            {error}
          </p>
        )}
        <Button
          type="submit"
          disabled={isGenerating}
          loading={isGenerating}
          className="mt-3 w-full"
        >
          {isGenerating ? '生成中…' : hasSession ? '重新生成' : '开始生成'}
        </Button>
      </form>

      {/* SSE 消息流展示区 */}
      <div className="flex-1 overflow-y-auto p-4">
        {!streamContent && !isGenerating && (
          <div className="flex h-full items-center justify-center text-gray-400">
            <p className="text-sm">输入需求描述后，AI 将实时生成 Agent 配置</p>
          </div>
        )}

        {isGenerating && !streamContent && (
          <div className="flex items-center gap-2 text-blue-600">
            <Spinner />
            <span className="text-sm">正在生成…</span>
          </div>
        )}

        {streamContent && (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">生成过程</p>
            <div className="rounded-lg bg-gray-50 p-3 text-sm leading-relaxed text-gray-700">
              {/* 保留换行格式 */}
              <pre className="whitespace-pre-wrap font-sans">{streamContent}</pre>
            </div>
            {/* 流结束时显示完成标记 */}
            {!isGenerating && <p className="text-xs text-green-600">生成完成，请在右侧确认配置</p>}
          </div>
        )}

        {/* 滚动锚点 */}
        <div ref={streamEndRef} />
      </div>
    </div>
  );
}
