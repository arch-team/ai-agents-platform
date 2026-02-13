// 知识库列表页面
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { KnowledgeList, KnowledgeCreateDialog } from '@/features/knowledge';

export default function KnowledgeListPage() {
  const navigate = useNavigate();
  const [showCreate, setShowCreate] = useState(false);

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">知识库管理</h1>
      <KnowledgeList
        onSelect={(id) => navigate(`/knowledge/${id}`)}
        onCreate={() => setShowCreate(true)}
      />
      <KnowledgeCreateDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSuccess={(id) => navigate(`/knowledge/${id}`)}
      />
    </div>
  );
}
