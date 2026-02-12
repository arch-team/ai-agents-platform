// Dashboard 页面 — 欢迎信息 + 快速操作 + 统计概览
import { Link } from 'react-router-dom';

import { useAuth } from '@/features/auth';
import { useAgents } from '@/features/agents';
import { useConversations } from '@/features/execution';
import { useTeamExecutions } from '@/features/team-executions';
import { Card, Spinner, AgentIcon, ChatIcon, TeamIcon } from '@/shared/ui';

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: conversationsData, isLoading: conversationsLoading } = useConversations();
  const { data: executionsData, isLoading: executionsLoading } = useTeamExecutions();

  const agentCount = agentsData?.total ?? 0;
  const conversationCount = conversationsData?.total ?? 0;
  const executionCount = executionsData?.total ?? 0;

  return (
    <div className="p-6">
      {/* 欢迎信息 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          欢迎回来{user?.name ? `，${user.name}` : ''}
        </h1>
        <p className="mt-1 text-gray-500">管理你的 AI Agent，开始智能对话</p>
      </div>

      {/* 统计概览 */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
            <AgentIcon className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Agent 总数</p>
            {agentsLoading ? (
              <Spinner size="sm" />
            ) : (
              <p className="text-2xl font-bold text-gray-900">{agentCount}</p>
            )}
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100">
            <ChatIcon className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">对话总数</p>
            {conversationsLoading ? (
              <Spinner size="sm" />
            ) : (
              <p className="text-2xl font-bold text-gray-900">{conversationCount}</p>
            )}
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100">
            <TeamIcon className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Team 执行</p>
            {executionsLoading ? (
              <Spinner size="sm" />
            ) : (
              <p className="text-2xl font-bold text-gray-900">{executionCount}</p>
            )}
          </div>
        </Card>
      </div>

      {/* 快速操作 */}
      <h2 className="mb-4 text-lg font-semibold text-gray-900">快速操作</h2>
      <div className="grid gap-4 sm:grid-cols-3">
        <Link
          to="/agents/create"
          className="group rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <h3 className="font-medium text-gray-900 group-hover:text-blue-600">创建 Agent</h3>
          <p className="mt-1 text-sm text-gray-500">配置新的 AI Agent，定义行为和角色</p>
        </Link>

        <Link
          to="/agents"
          className="group rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <h3 className="font-medium text-gray-900 group-hover:text-blue-600">查看 Agent 列表</h3>
          <p className="mt-1 text-sm text-gray-500">管理和浏览所有已创建的 Agent</p>
        </Link>

        <Link
          to="/team-executions"
          className="group rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <h3 className="font-medium text-gray-900 group-hover:text-purple-600">Team Execution</h3>
          <p className="mt-1 text-sm text-gray-500">协调多个 Agent 执行复杂任务</p>
        </Link>
      </div>
    </div>
  );
}
