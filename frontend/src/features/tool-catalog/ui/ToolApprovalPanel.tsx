// 工具审批面板组件 (ADMIN)

import { useState } from 'react';

import { Button } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useApproveTool, useRejectTool } from '../api/queries';
import type { Tool } from '../api/types';

interface ToolApprovalPanelProps {
  tool: Tool;
}

export function ToolApprovalPanel({ tool }: ToolApprovalPanelProps) {
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approveMutation = useApproveTool();
  const rejectMutation = useRejectTool();

  // 仅在 PENDING_REVIEW 状态时显示审批面板
  if (tool.status !== 'pending_review') {
    return null;
  }

  const handleApprove = async () => {
    setError(null);
    try {
      await approveMutation.mutateAsync(tool.id);
    } catch (err) {
      setError(extractApiError(err, '审批通过失败'));
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    setError(null);
    try {
      await rejectMutation.mutateAsync({ id: tool.id, reason: rejectReason });
      setShowRejectForm(false);
      setRejectReason('');
    } catch (err) {
      setError(extractApiError(err, '审批拒绝失败'));
    }
  };

  return (
    <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-yellow-800">审批操作</h3>

      {error && (
        <div
          role="alert"
          className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {showRejectForm ? (
        <div className="space-y-3">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="reject-reason" className="text-sm font-medium text-gray-700">
              拒绝原因
            </label>
            <textarea
              id="reject-reason"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="请输入拒绝原因"
              rows={3}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              aria-required="true"
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setShowRejectForm(false);
                setRejectReason('');
              }}
            >
              取消
            </Button>
            <Button
              size="sm"
              variant="secondary"
              loading={rejectMutation.isPending}
              disabled={!rejectReason.trim()}
              onClick={handleReject}
            >
              确认拒绝
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2">
          <Button size="sm" loading={approveMutation.isPending} onClick={handleApprove}>
            审批通过
          </Button>
          <Button size="sm" variant="outline" onClick={() => setShowRejectForm(true)}>
            拒绝
          </Button>
        </div>
      )}
    </div>
  );
}
