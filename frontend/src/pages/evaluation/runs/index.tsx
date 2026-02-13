// 评估运行页面

import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { EvaluationRunList, EvaluationResults } from '@/features/evaluation';
import { Button } from '@/shared/ui';

export default function EvaluationRunsPage() {
  const [searchParams] = useSearchParams();
  const initialRunId = searchParams.get('runId') ? Number(searchParams.get('runId')) : null;
  const [selectedRunId, setSelectedRunId] = useState<number | null>(initialRunId);

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">评估运行</h1>
        {selectedRunId && (
          <Button variant="outline" size="sm" onClick={() => setSelectedRunId(null)}>
            返回列表
          </Button>
        )}
      </div>

      {selectedRunId ? (
        <EvaluationResults runId={selectedRunId} />
      ) : (
        <EvaluationRunList onSelect={(id) => setSelectedRunId(id)} />
      )}
    </div>
  );
}
