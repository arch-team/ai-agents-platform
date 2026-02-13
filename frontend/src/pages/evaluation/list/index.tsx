// 测试集列表页面

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { TestSuiteList, TestSuiteCreateDialog } from '@/features/evaluation';

export default function EvaluationListPage() {
  const navigate = useNavigate();
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">评估管理</h1>
      <TestSuiteList
        onSelect={(id) => navigate(`/evaluation/${id}`)}
        onCreate={() => setShowCreateDialog(true)}
      />

      {showCreateDialog && (
        <TestSuiteCreateDialog
          onSuccess={(suiteId) => navigate(`/evaluation/${suiteId}`)}
          onClose={() => setShowCreateDialog(false)}
        />
      )}
    </div>
  );
}
