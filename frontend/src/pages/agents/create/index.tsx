// Agent 创建页面
import { useNavigate } from 'react-router-dom';

import { AgentCreateForm } from '@/features/agents';
import { Card } from '@/shared/ui';

export default function AgentCreatePage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">创建 Agent</h1>
      <Card>
        <AgentCreateForm
          onSuccess={(id) => navigate(`/agents/${id}`)}
          onCancel={() => navigate('/agents')}
        />
      </Card>
    </div>
  );
}
