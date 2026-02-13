// 测试集详情页面

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { TestSuiteDetail, RunEvaluationDialog, useTestSuite } from '@/features/evaluation';
import { parseNumericParam } from '@/shared/lib/parseNumericParam';

export default function EvaluationDetailPage() {
  const { suiteId } = useParams<{ suiteId: string }>();
  const navigate = useNavigate();
  const id = parseNumericParam(suiteId);
  const { data: suite } = useTestSuite(id);
  const [showRunDialog, setShowRunDialog] = useState(false);

  if (!id) {
    return null;
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <TestSuiteDetail
        suiteId={id}
        onBack={() => navigate('/evaluation')}
        onRunEvaluation={() => setShowRunDialog(true)}
      />

      {showRunDialog && suite && (
        <RunEvaluationDialog
          suiteId={id}
          suiteName={suite.name}
          onSuccess={(runId) => navigate(`/evaluation/runs?runId=${runId}`)}
          onClose={() => setShowRunDialog(false)}
        />
      )}
    </div>
  );
}
