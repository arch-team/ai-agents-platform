import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

import { Spinner } from '@/shared/ui';

import { ProtectedRoute } from './ProtectedRoute';

// 路由级代码分割
const LoginPage = lazy(() => import('@/pages/login'));
const RegisterPage = lazy(() => import('@/pages/register'));
const DashboardPage = lazy(() => import('@/pages/dashboard'));
const AgentListPage = lazy(() => import('@/pages/agents/list'));
const AgentCreatePage = lazy(() => import('@/pages/agents/create'));
const AgentDetailPage = lazy(() => import('@/pages/agents/detail'));
const ChatPage = lazy(() => import('@/pages/chat'));
const TeamExecutionPage = lazy(() => import('@/pages/team-executions'));
const NotFoundPage = lazy(() => import('@/pages/not-found'));

// 延迟加载布局组件
const AppLayout = lazy(() => import('@/widgets/layout').then((m) => ({ default: m.AppLayout })));

export function AppRoutes() {
  return (
    <Suspense fallback={<Spinner fullScreen />}>
      <Routes>
        {/* 公开路由 */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* 需认证的路由 */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/agents" element={<AgentListPage />} />
            <Route path="/agents/create" element={<AgentCreatePage />} />
            <Route path="/agents/:agentId" element={<AgentDetailPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/chat/:conversationId" element={<ChatPage />} />
            <Route path="/team-executions" element={<TeamExecutionPage />} />
          </Route>
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
