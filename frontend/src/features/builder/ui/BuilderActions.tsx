// Builder 底部操作栏 — 阶段感知按钮组
// | input      | [开始生成]                        |
// | generating | [取消生成]                        |
// | configure  | [取消] [继续调整] [开始测试 →]    |
// | testing    | [返回修改] [上线发布 ✓]           |

import { Button } from '@/shared/ui';

import type { BuilderPhase } from '../api/types';
import {
  useBuilderBlueprint,
  useBuilderIsConfirming,
  useBuilderIsGenerating,
  useBuilderPhase,
  useBuilderSessionId,
} from '../model/store';

interface BuilderActionsProps {
  onCancel: () => void;
  onContinueAdjust?: () => void;
  onStartTesting: () => void;
  onGoLive: () => void;
  onBackToEdit: () => void;
}

export function BuilderActions({
  onCancel,
  onContinueAdjust,
  onStartTesting,
  onGoLive,
  onBackToEdit,
}: BuilderActionsProps) {
  const sessionId = useBuilderSessionId();
  const phase = useBuilderPhase();
  const blueprint = useBuilderBlueprint();
  const isGenerating = useBuilderIsGenerating();
  const isConfirming = useBuilderIsConfirming();

  // input 阶段不显示底栏（提交按钮在 Chat 组件内）
  if (phase === 'input' && !sessionId) return null;

  return (
    <div className="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-3">
      <div>{/* 左侧留空或放置辅助信息 */}</div>

      <div className="flex items-center gap-3">
        <PhaseButtons
          phase={phase}
          isGenerating={isGenerating}
          isConfirming={isConfirming}
          hasBlueprint={!!blueprint}
          onCancel={onCancel}
          onContinueAdjust={onContinueAdjust}
          onStartTesting={onStartTesting}
          onGoLive={onGoLive}
          onBackToEdit={onBackToEdit}
        />
      </div>
    </div>
  );
}

// ── 内部子组件 ──

interface PhaseButtonsProps {
  phase: BuilderPhase;
  isGenerating: boolean;
  isConfirming: boolean;
  hasBlueprint: boolean;
  onCancel: () => void;
  onContinueAdjust?: () => void;
  onStartTesting: () => void;
  onGoLive: () => void;
  onBackToEdit: () => void;
}

function PhaseButtons({
  phase,
  isGenerating,
  isConfirming,
  hasBlueprint,
  onCancel,
  onContinueAdjust,
  onStartTesting,
  onGoLive,
  onBackToEdit,
}: PhaseButtonsProps) {
  switch (phase) {
    case 'generating':
      return (
        <Button variant="outline" onClick={onCancel}>
          取消生成
        </Button>
      );

    case 'configure':
      return (
        <>
          <Button variant="outline" onClick={onCancel} disabled={isConfirming}>
            取消
          </Button>
          {onContinueAdjust && (
            <Button variant="outline" onClick={onContinueAdjust} disabled={isGenerating}>
              继续调整
            </Button>
          )}
          <Button
            onClick={onStartTesting}
            disabled={!hasBlueprint || isGenerating || isConfirming}
            loading={isConfirming}
          >
            开始测试 →
          </Button>
        </>
      );

    case 'testing':
      return (
        <>
          <Button variant="outline" onClick={onBackToEdit}>
            ← 返回修改
          </Button>
          <Button onClick={onGoLive} loading={isConfirming}>
            上线发布 ✓
          </Button>
        </>
      );

    default:
      return null;
  }
}
