// Team Execution 页面 — 左侧创建+列表，右侧详情+日志

import { useState, useCallback } from 'react';

import { useAuthToken } from '@/features/auth';
import { useAgents } from '@/features/agents';
import {
  TeamExecForm,
  TeamExecList,
  TeamExecDetail,
  useCreateTeamExecution,
  useTeamExecutionStream,
} from '@/features/team-executions';
import type { TeamExecution } from '@/features/team-executions';
import { extractApiError } from '@/shared/lib/extractApiError';
import { ErrorMessage } from '@/shared/ui';

export default function TeamExecutionPage() {
  const token = useAuthToken();
  const { data: agentsData } = useAgents();
  const createMutation = useCreateTeamExecution();
  const { startStream } = useTeamExecutionStream(token);

  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<TeamExecution | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (prompt: string) => {
    if (!selectedAgentId) return;
    setSubmitError(null);
    try {
      const execution = await createMutation.mutateAsync({
        agent_id: selectedAgentId,
        prompt,
      });
      setSelectedExecution(execution);
      // 创建后自动开始流式监听
      startStream(execution.id);
    } catch (err) {
      setSubmitError(extractApiError(err, '创建执行失败'));
    }
  };

  const handleSelectExecution = (execution: TeamExecution) => {
    setSelectedExecution(execution);
  };

  const handleStartStream = useCallback(
    (id: number) => {
      startStream(id);
    },
    [startStream],
  );

  return (
    <div className="flex h-full">
      {/* 左侧面板: 创建表单 + 执行列表 */}
      <div className="flex w-80 shrink-0 flex-col border-r border-gray-200 bg-white">
        {/* 创建表单 */}
        <div className="border-b border-gray-200 p-4">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">新建执行</h2>
          <TeamExecForm
            agents={agentsData?.items ?? []}
            selectedAgentId={selectedAgentId}
            onSelectAgent={setSelectedAgentId}
            onSubmit={handleSubmit}
            isSubmitting={createMutation.isPending}
          />
          {submitError && <ErrorMessage error={submitError} className="mt-3" />}
        </div>

        {/* 执行列表 */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-4 pt-4 pb-2">
            <h2 className="text-sm font-semibold text-gray-700">执行历史</h2>
          </div>
          <TeamExecList
            selectedId={selectedExecution?.id ?? null}
            onSelect={handleSelectExecution}
          />
        </div>
      </div>

      {/* 右侧面板: 执行详情 + 日志 */}
      <div className="flex-1 overflow-hidden">
        {selectedExecution ? (
          <TeamExecDetail
            executionId={selectedExecution.id}
            onStartStream={handleStartStream}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <p className="text-gray-400">选择一个执行记录或创建新的 Team Execution</p>
              <p className="mt-1 text-sm text-gray-300">
                Agent Teams 可以协调多个 Agent 完成复杂任务
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
