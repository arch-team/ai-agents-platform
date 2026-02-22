// Builder 底部操作栏 — 确认创建 Agent / 取消重置

import { Button } from '@/shared/ui';

import {
  useBuilderGeneratedConfig,
  useBuilderIsConfirming,
  useBuilderIsGenerating,
  useBuilderSessionId,
} from '../model/store';

interface BuilderActionsProps {
  /** 确认创建 Agent 回调 */
  onConfirm: (sessionId: number) => void;
  /** 取消重置回调 */
  onCancel: () => void;
}

export function BuilderActions({ onConfirm, onCancel }: BuilderActionsProps) {
  const sessionId = useBuilderSessionId();
  const generatedConfig = useBuilderGeneratedConfig();
  const isGenerating = useBuilderIsGenerating();
  const isConfirming = useBuilderIsConfirming();

  // 仅在生成完成且有配置时才显示操作按钮
  const canConfirm = !!sessionId && !!generatedConfig && !isGenerating;

  if (!sessionId) {
    return null;
  }

  return (
    <div className="flex items-center justify-end gap-3 border-t border-gray-200 bg-white px-6 py-4">
      <Button variant="outline" onClick={onCancel} disabled={isConfirming}>
        取消
      </Button>
      <Button
        onClick={() => {
          if (sessionId !== null) onConfirm(sessionId);
        }}
        disabled={!canConfirm}
        loading={isConfirming}
      >
        确认创建 Agent
      </Button>
    </div>
  );
}
