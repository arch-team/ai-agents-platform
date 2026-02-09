// Agent 列表页面
import { useNavigate } from 'react-router-dom';

import { AgentList } from '@/features/agents';

export default function AgentListPage() {
  const navigate = useNavigate();

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Agent 管理</h1>
      <AgentList
        onSelect={(id) => navigate(`/agents/${id}`)}
        onEdit={(id) => navigate(`/agents/${id}`)}
        onCreate={() => navigate('/agents/create')}
      />
    </div>
  );
}
