// 模板列表页面
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { TemplateList, TemplateCreateDialog } from '@/features/templates';

export default function TemplateListPage() {
  const navigate = useNavigate();
  const [showCreate, setShowCreate] = useState(false);

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">模板管理</h1>
      <TemplateList
        onSelect={(id) => navigate(`/templates/${id}`)}
        onCreate={() => setShowCreate(true)}
      />
      <TemplateCreateDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSuccess={(id) => navigate(`/templates/${id}`)}
      />
    </div>
  );
}
