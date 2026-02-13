// Agent 详情页面
import { useNavigate, useParams } from 'react-router-dom';

import { useAgent, useActivateAgent, useArchiveAgent, AgentStatusBadge } from '@/features/agents';
import { useConversations, useCreateConversation } from '@/features/execution';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDate, formatDateTime } from '@/shared/lib/formatDate';
import { Button, Card, Spinner, ErrorMessage } from '@/shared/ui';

export default function AgentDetailPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const id = agentId ? Number(agentId) : undefined;

  const { data: agent, isLoading, error } = useAgent(id);
  const { data: conversationsData } = useConversations(id);
  const activateMutation = useActivateAgent();
  const archiveMutation = useArchiveAgent();
  const createConversation = useCreateConversation();

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
      {activateMutation.isError && (
        <div className="mb-4">
          <ErrorMessage error={extractApiError(activateMutation.error, '激活 Agent 失败')} />
        </div>
      )}
      {archiveMutation.isError && (
        <div className="mb-4">
          <ErrorMessage error={extractApiError(archiveMutation.error, '归档 Agent 失败')} />
        </div>
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

      {/* Agent 详情信息 */}
      <Card className="mb-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">配置信息</h2>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">模型</dt>
            <dd className="mt-1 text-sm text-gray-900">{agent.config.model_id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">温度</dt>
            <dd className="mt-1 text-sm text-gray-900">{agent.config.temperature}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">最大 Token 数</dt>
            <dd className="mt-1 text-sm text-gray-900">{agent.config.max_tokens}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">创建时间</dt>
            <dd className="mt-1 text-sm text-gray-900">{formatDateTime(agent.created_at)}</dd>
          </div>
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
