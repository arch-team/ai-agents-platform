// Agent 详情页面
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import {
  useAgent,
  useActivateAgent,
  useArchiveAgent,
  usePreviewAgent,
  AgentStatusBadge,
  MemoryPanel,
} from '@/features/agents';
import { useConversations, useCreateConversation } from '@/features/execution';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDate, formatDateTime } from '@/shared/lib/formatDate';
import { parseNumericParam } from '@/shared/lib/parseNumericParam';
import { Button, Card, Spinner, ErrorMessage, Textarea } from '@/shared/ui';

export default function AgentDetailPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const id = parseNumericParam(agentId);

  const { data: agent, isLoading, error } = useAgent(id);
  const { data: conversationsData } = useConversations(id);
  const activateMutation = useActivateAgent();
  const archiveMutation = useArchiveAgent();
  const createConversation = useCreateConversation();

  // 预览面板状态
  const [showPreview, setShowPreview] = useState(false);
  const [previewPrompt, setPreviewPrompt] = useState('');
  const previewMutation = usePreviewAgent();

  const handleStartChat = async () => {
    if (!agent) return;
    try {
      const conversation = await createConversation.mutateAsync({
        agent_id: agent.id,
        title: `与 ${agent.name} 的对话`,
      });
      navigate(`/chat/${conversation.id}`);
    } catch {
      // 错误由 mutation 状态处理
    }
  };

  const handleSendPreview = () => {
    if (!agent || !previewPrompt.trim()) return;
    previewMutation.mutate({ agentId: agent.id, prompt: previewPrompt.trim() });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="p-6">
        <ErrorMessage error={extractApiError(error, '加载 Agent 详情失败')} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      {/* 操作错误提示 */}
      {[
        { mutation: activateMutation, message: '激活 Agent 失败' },
        { mutation: archiveMutation, message: '归档 Agent 失败' },
      ].map(
        ({ mutation, message }) =>
          mutation.isError && (
            <div key={message} className="mb-4">
              <ErrorMessage error={extractApiError(mutation.error, message)} />
            </div>
          ),
      )}

      {/* 标题和操作 */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
            <AgentStatusBadge status={agent.status} />
          </div>
          {agent.description && <p className="mt-2 text-gray-600">{agent.description}</p>}
        </div>
        <div className="flex gap-2">
          {agent.status === 'draft' && (
            <Button
              variant="primary"
              size="sm"
              loading={activateMutation.isPending}
              onClick={() => activateMutation.mutate(agent.id)}
              aria-label={`激活 ${agent.name}`}
            >
              激活
            </Button>
          )}
          {agent.status === 'active' && (
            <>
              <Button
                variant="primary"
                size="sm"
                loading={createConversation.isPending}
                onClick={handleStartChat}
                aria-label={`与 ${agent.name} 开始对话`}
              >
                开始对话
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowPreview(!showPreview);
                  previewMutation.reset();
                }}
                aria-expanded={showPreview}
                aria-controls="preview-panel"
              >
                测试 Agent
              </Button>
              <Button
                variant="outline"
                size="sm"
                loading={archiveMutation.isPending}
                onClick={() => archiveMutation.mutate(agent.id)}
                aria-label={`归档 ${agent.name}`}
              >
                归档
              </Button>
            </>
          )}
          <Button variant="outline" size="sm" onClick={() => navigate('/agents')}>
            返回列表
          </Button>
        </div>
      </div>

      {/* 测试 Agent 预览面板 */}
      {showPreview && (
        <Card id="preview-panel" className="mb-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">测试 Agent</h2>
            <button
              type="button"
              className="text-sm text-gray-500 hover:text-gray-700"
              onClick={() => setShowPreview(false)}
              aria-label="关闭测试面板"
            >
              关闭
            </button>
          </div>

          <div className="space-y-4">
            <Textarea
              label="测试消息"
              placeholder="输入测试消息..."
              rows={3}
              value={previewPrompt}
              onChange={(e) => setPreviewPrompt(e.target.value)}
              maxLength={2000}
            />

            <div className="flex justify-end">
              <Button
                size="sm"
                loading={previewMutation.isPending}
                disabled={!previewPrompt.trim()}
                onClick={handleSendPreview}
              >
                发送测试
              </Button>
            </div>

            {/* 预览结果 */}
            {previewMutation.isPending && (
              <div className="flex items-center justify-center py-6">
                <Spinner />
              </div>
            )}

            {previewMutation.isError && (
              <ErrorMessage error={extractApiError(previewMutation.error, '预览请求失败')} />
            )}

            {previewMutation.data && (
              <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                <h3 className="mb-2 text-sm font-medium text-gray-700">预览结果</h3>
                <p className="whitespace-pre-wrap text-sm text-gray-900">
                  {previewMutation.data.content}
                </p>
                <div className="mt-3 flex gap-4 border-t border-gray-200 pt-3 text-xs text-gray-500">
                  <span>模型: {previewMutation.data.model_id}</span>
                  <span>
                    Token: 输入 {previewMutation.data.tokens_input} / 输出{' '}
                    {previewMutation.data.tokens_output}
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Agent 详情信息 */}
      <Card className="mb-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">配置信息</h2>
        <dl className="grid gap-4 sm:grid-cols-2">
          {[
            { label: '模型', value: agent.config.model_id },
            { label: '温度', value: agent.config.temperature },
            { label: '最大 Token 数', value: agent.config.max_tokens },
            { label: '记忆', value: agent.config.enable_memory ? '已启用' : '未启用' },
            { label: '创建时间', value: formatDateTime(agent.created_at) },
          ].map(({ label, value }) => (
            <div key={label}>
              <dt className="text-sm font-medium text-gray-500">{label}</dt>
              <dd className="mt-1 text-sm text-gray-900">{value}</dd>
            </div>
          ))}
        </dl>

        {agent.system_prompt && (
          <div className="mt-4 border-t border-gray-100 pt-4">
            <dt className="text-sm font-medium text-gray-500">系统提示词</dt>
            <dd className="mt-1 whitespace-pre-wrap rounded-md bg-gray-50 p-3 text-sm text-gray-700">
              {agent.system_prompt}
            </dd>
          </div>
        )}
      </Card>

      {/* 记忆管理面板 — 仅当 enable_memory 开启时展示 */}
      {agent.config.enable_memory && (
        <div className="mb-6">
          <MemoryPanel agentId={agent.id} />
        </div>
      )}

      {/* 对话历史 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">对话历史</h2>
        {!conversationsData?.items.length ? (
          <p className="text-sm text-gray-500">暂无对话记录</p>
        ) : (
          <ul className="divide-y divide-gray-100" role="list" aria-label="对话历史">
            {conversationsData.items.map((conv) => (
              <li key={conv.id}>
                <button
                  type="button"
                  onClick={() => navigate(`/chat/${conv.id}`)}
                  aria-label={`查看对话: ${conv.title || `对话 #${conv.id}`}`}
                  className="flex w-full items-center justify-between px-2 py-3 text-left hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {conv.title || `对话 #${conv.id}`}
                    </p>
                    <p className="text-xs text-gray-500">{conv.message_count} 条消息</p>
                  </div>
                  <time className="text-xs text-gray-400" dateTime={conv.updated_at}>
                    {formatDate(conv.updated_at)}
                  </time>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
