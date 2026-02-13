// 创建测试集对话框组件

import { useState } from 'react';

import { extractApiError } from '@/shared/lib/extractApiError';
import { Button, Input, Textarea, ErrorMessage } from '@/shared/ui';

import { useCreateTestSuite } from '../api/queries';

interface TestSuiteCreateDialogProps {
  /** 关联的 Agent ID */
  agentId?: number;
  /** 创建成功回调 */
  onSuccess?: (suiteId: number) => void;
  /** 关闭对话框 */
  onClose: () => void;
}

export function TestSuiteCreateDialog({ agentId, onSuccess, onClose }: TestSuiteCreateDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [agentIdInput, setAgentIdInput] = useState(agentId?.toString() ?? '');
  const createMutation = useCreateTestSuite();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsedAgentId = Number(agentIdInput);
    if (!name.trim() || !parsedAgentId) return;

    try {
      const suite = await createMutation.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
        agent_id: parsedAgentId,
      });
      onSuccess?.(suite.id);
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
      aria-labelledby="create-suite-title"
    >
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 id="create-suite-title" className="mb-4 text-lg font-semibold text-gray-900">
          创建测试集
        </h2>

        {createMutation.isError && (
          <div className="mb-4">
            <ErrorMessage error={extractApiError(createMutation.error, '创建测试集失败')} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="名称"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="输入测试集名称"
            required
            autoFocus
          />
          <Textarea
            label="描述"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="输入测试集描述（可选）"
            rows={3}
          />
          <Input
            label="Agent ID"
            type="number"
            value={agentIdInput}
            onChange={(e) => setAgentIdInput(e.target.value)}
            placeholder="输入关联的 Agent ID"
            required
            min={1}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" type="button" onClick={onClose}>
              取消
            </Button>
            <Button
              size="sm"
              type="submit"
              loading={createMutation.isPending}
              disabled={!name.trim() || !agentIdInput}
            >
              创建
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
