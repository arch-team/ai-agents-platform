// Team Execution 详情面板 — 执行信息 + 日志 + SSE 流式输出

import { useEffect, useRef } from 'react';

import { formatDateTime } from '@/shared/lib/formatDate';
import { Button, Card, Spinner, ErrorMessage } from '@/shared/ui';

import { useTeamExecution, useTeamExecutionLogs, useCancelTeamExecution } from '../api/queries';
import { useStreamLogs, useIsTeamStreaming, useTeamExecError } from '../model/store';

import { TeamExecStatusBadge } from './TeamExecStatusBadge';

interface TeamExecDetailProps {
  executionId: number;
  onStartStream: (id: number) => void;
}

export function TeamExecDetail({ executionId, onStartStream }: TeamExecDetailProps) {
  const { data: execution, isLoading } = useTeamExecution(executionId);
  const { data: logs } = useTeamExecutionLogs(executionId);
  const cancelMutation = useCancelTeamExecution();
  const streamLogs = useStreamLogs();
  const isStreaming = useIsTeamStreaming();
  const streamError = useTeamExecError();
  const logsEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到日志底部
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [streamLogs, logs]);

  // 运行中的执行自动开始 SSE 流
  useEffect(() => {
    if (execution?.status === 'running' && !isStreaming) {
      onStartStream(executionId);
    }
  }, [execution?.status, executionId, isStreaming, onStartStream]);

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!execution) {
    return <ErrorMessage error="无法加载执行详情" />;
  }

  // 优先显示 SSE 流式日志，其次显示 API 拉取的日志
  const displayLogs = streamLogs.length > 0 ? streamLogs : (logs ?? []).map((log) => ({
    sequence: log.sequence,
    content: log.content,
    agentName: log.agent_name,
  }));

  return (
    <div className="flex h-full flex-col">
      {/* 执行概览 */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">执行 #{execution.id}</h2>
            <p className="mt-1 text-sm text-gray-500">{formatDateTime(execution.created_at)}</p>
          </div>
          <div className="flex items-center gap-3">
            <TeamExecStatusBadge status={execution.status} />
            {(execution.status === 'pending' || execution.status === 'running') && (
              <Button
                variant="outline"
                size="sm"
                loading={cancelMutation.isPending}
                onClick={() => cancelMutation.mutate(execution.id)}
                aria-label={`取消执行 #${execution.id}`}
              >
                取消执行
              </Button>
            )}
          </div>
        </div>

        {/* 提示词 */}
        <div className="mt-3">
          <p className="text-sm font-medium text-gray-500">提示词</p>
          <p className="mt-1 whitespace-pre-wrap rounded-md bg-gray-50 p-3 text-sm text-gray-700">
            {execution.prompt}
          </p>
        </div>

        {/* 执行结果 */}
        {execution.result && (
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-500">执行结果</p>
            <p className="mt-1 whitespace-pre-wrap rounded-md bg-green-50 p-3 text-sm text-gray-700">
              {execution.result}
            </p>
          </div>
        )}

        {/* 错误信息 */}
        {execution.error && (
          <div className="mt-3">
            <ErrorMessage error={execution.error} />
          </div>
        )}
      </div>

      {/* 日志区域 */}
      <div className="flex-1 overflow-y-auto p-4" role="log" aria-label="执行日志" aria-live="polite">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">执行日志</h3>

        {streamError && <ErrorMessage error={streamError} className="mb-3" />}

        {displayLogs.length === 0 && !isStreaming ? (
          <p className="text-sm text-gray-400">暂无日志</p>
        ) : (
          <div className="space-y-2">
            {displayLogs.map((log, index) => (
              <LogEntry
                key={`${log.sequence}-${index}`}
                sequence={log.sequence}
                agentName={log.agentName}
                content={log.content}
              />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <Spinner size="sm" />
                <span>接收中...</span>
              </div>
            )}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}

// 日志条目子组件
function LogEntry({
  sequence,
  agentName,
  content,
}: {
  sequence: number;
  agentName: string;
  content: string;
}) {
  return (
    <Card className="!p-3">
      <div className="mb-1 flex items-center gap-2">
        <span className="text-xs font-mono text-gray-400">#{sequence}</span>
        {agentName && (
          <span className="rounded bg-purple-100 px-1.5 py-0.5 text-xs font-medium text-purple-700">
            {agentName}
          </span>
        )}
      </div>
      <p className="whitespace-pre-wrap text-sm text-gray-800">{content}</p>
    </Card>
  );
}
