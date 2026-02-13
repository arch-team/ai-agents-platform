// 测试用例表单组件（添加/编辑）

import { useState } from 'react';

import { extractApiError } from '@/shared/lib/extractApiError';
import { Button, Textarea, ErrorMessage } from '@/shared/ui';

import { useCreateTestCase, useUpdateTestCase } from '../api/queries';
import type { TestCase } from '../api/types';

interface TestCaseFormProps {
  suiteId: number;
  /** 编辑模式时传入已有用例 */
  editCase?: TestCase;
  /** 提交成功回调 */
  onSuccess?: () => void;
  /** 取消回调 */
  onCancel?: () => void;
}

// 注意: 当 editCase 变化时，调用方应使用 key={editCase?.id} 确保组件重新创建
export function TestCaseForm({ suiteId, editCase, onSuccess, onCancel }: TestCaseFormProps) {
  const [inputPrompt, setInputPrompt] = useState(editCase?.input_prompt ?? '');
  const [expectedOutput, setExpectedOutput] = useState(editCase?.expected_output ?? '');
  const [evaluationCriteria, setEvaluationCriteria] = useState(editCase?.evaluation_criteria ?? '');

  const createMutation = useCreateTestCase();
  const updateMutation = useUpdateTestCase();
  const isEditing = !!editCase;
  const mutation = isEditing ? updateMutation : createMutation;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputPrompt.trim()) return;

    try {
      if (isEditing && editCase) {
        await updateMutation.mutateAsync({
          suiteId,
          caseId: editCase.id,
          input_prompt: inputPrompt.trim(),
          expected_output: expectedOutput.trim(),
          evaluation_criteria: evaluationCriteria.trim(),
        });
      } else {
        await createMutation.mutateAsync({
          suiteId,
          input_prompt: inputPrompt.trim(),
          expected_output: expectedOutput.trim() || undefined,
          evaluation_criteria: evaluationCriteria.trim() || undefined,
        });
      }
      // 重置表单
      if (!isEditing) {
        setInputPrompt('');
        setExpectedOutput('');
        setEvaluationCriteria('');
      }
      onSuccess?.();
    } catch {
      // 错误由 mutation 状态处理
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-900">
        {isEditing ? '编辑测试用例' : '添加测试用例'}
      </h3>

      {mutation.isError && (
        <ErrorMessage
          error={extractApiError(mutation.error, isEditing ? '更新测试用例失败' : '添加测试用例失败')}
        />
      )}

      <Textarea
        label="输入提示词"
        value={inputPrompt}
        onChange={(e) => setInputPrompt(e.target.value)}
        placeholder="输入用于测试的提示词"
        rows={3}
        required
      />
      <Textarea
        label="期望输出"
        value={expectedOutput}
        onChange={(e) => setExpectedOutput(e.target.value)}
        placeholder="输入期望的输出结果（可选）"
        rows={3}
      />
      <Textarea
        label="评分标准"
        value={evaluationCriteria}
        onChange={(e) => setEvaluationCriteria(e.target.value)}
        placeholder="输入评分标准（可选）"
        rows={2}
      />
      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button variant="outline" size="sm" type="button" onClick={onCancel}>
            取消
          </Button>
        )}
        <Button
          size="sm"
          type="submit"
          loading={mutation.isPending}
          disabled={!inputPrompt.trim()}
        >
          {isEditing ? '保存' : '添加'}
        </Button>
      </div>
    </form>
  );
}
