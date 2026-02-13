// Dashboard 页面 — 欢迎信息 + 快速操作 + 统计概览
import { Link } from 'react-router-dom';

import { useAuth } from '@/features/auth';
import { useDashboardSummary } from '@/features/dashboard';
import { AgentIcon, ChatIcon, TeamIcon, StatCard } from '@/shared/ui';

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: summary, isLoading } = useDashboardSummary();

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
        <StatCard
          icon={<AgentIcon className="h-6 w-6 text-blue-600" />}
          iconBgClass="bg-blue-100"
          label="Agent 总数"
          value={summary?.agents_total ?? 0}
          isLoading={isLoading}
        />
        <StatCard
          icon={<ChatIcon className="h-6 w-6 text-green-600" />}
          iconBgClass="bg-green-100"
          label="对话总数"
          value={summary?.conversations_total ?? 0}
          isLoading={isLoading}
        />
        <StatCard
          icon={<TeamIcon className="h-6 w-6 text-purple-600" />}
          iconBgClass="bg-purple-100"
          label="Team 执行"
          value={summary?.team_executions_total ?? 0}
          isLoading={isLoading}
        />
      </div>

      {/* 快速操作 */}
      <h2 className="mb-4 text-lg font-semibold text-gray-900">快速操作</h2>
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { to: '/agents/create', title: '创建 Agent', desc: '配置新的 AI Agent，定义行为和角色', hoverColor: 'group-hover:text-blue-600' },
          { to: '/agents', title: '查看 Agent 列表', desc: '管理和浏览所有已创建的 Agent', hoverColor: 'group-hover:text-blue-600' },
          { to: '/team-executions', title: 'Team Execution', desc: '协调多个 Agent 执行复杂任务', hoverColor: 'group-hover:text-purple-600' },
        ].map(({ to, title, desc, hoverColor }) => (
          <Link
            key={to}
            to={to}
            className="group rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <h3 className={`font-medium text-gray-900 ${hoverColor}`}>{title}</h3>
            <p className="mt-1 text-sm text-gray-500">{desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
