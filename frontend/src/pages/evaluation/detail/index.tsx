// 测试集详情页面

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import {
  TestSuiteDetail,
  RunEvaluationDialog,
  useTestSuite,
  PipelineList,
  ModelComparisonChart,
  useEvalPipelines,
} from '@/features/evaluation';
import { parseNumericParam } from '@/shared/lib/parseNumericParam';

export default function EvaluationDetailPage() {
  const { suiteId } = useParams<{ suiteId: string }>();
  const navigate = useNavigate();
  const id = parseNumericParam(suiteId);
  const { data: suite } = useTestSuite(id);
  const { data: pipelines } = useEvalPipelines(id);
  const [showRunDialog, setShowRunDialog] = useState(false);

  if (!id) {
    return null;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6">
      <TestSuiteDetail
        suiteId={id}
        onBack={() => navigate('/evaluation')}
        onRunEvaluation={() => setShowRunDialog(true)}
      />

      {/* Pipeline 运行 */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Pipeline 运行</h2>
        <PipelineList suiteId={id} />
      </section>

      {/* 模型评分对比 */}
      {pipelines && pipelines.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">模型评分对比</h2>
          <ModelComparisonChart pipelines={pipelines} />
        </section>
      )}

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
