// 发起评估对话框组件

import { extractApiError } from '@/shared/lib/extractApiError';
import { Button, ErrorMessage } from '@/shared/ui';

import { useCreateEvaluationRun } from '../api/queries';

interface RunEvaluationDialogProps {
  suiteId: number;
  suiteName: string;
  onSuccess?: (runId: number) => void;
  onClose: () => void;
}

export function RunEvaluationDialog({
  suiteId,
  suiteName,
  onSuccess,
  onClose,
}: RunEvaluationDialogProps) {
  const createRunMutation = useCreateEvaluationRun();

  const handleConfirm = async () => {
    try {
      const run = await createRunMutation.mutateAsync({ suite_id: suiteId });
      onSuccess?.(run.id);
      onClose();
    } catch {
      // 错误由 mutation 状态处理
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="run-evaluation-title"
    >
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h2 id="run-evaluation-title" className="mb-4 text-lg font-semibold text-gray-900">
          发起评估
        </h2>

        {createRunMutation.isError && (
          <div className="mb-4">
            <ErrorMessage error={extractApiError(createRunMutation.error, '创建评估运行失败')} />
          </div>
        )}

        <p className="mb-6 text-sm text-gray-600">
          确认对测试集 <span className="font-medium text-gray-900">{suiteName}</span> 发起评估运行？
          这将使用测试集中的所有用例对 Agent 进行评估。
        </p>

        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose}>
            取消
          </Button>
          <Button size="sm" loading={createRunMutation.isPending} onClick={handleConfirm}>
            确认发起
          </Button>
        </div>
      </div>
    </div>
  );
}
