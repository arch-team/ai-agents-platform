// 评估运行状态徽章组件
import { StatusBadge } from '@/shared/ui';

import type { EvaluationRunStatus } from '../api/types';

import { RUN_STATUS_BADGE_CONFIG } from './runStatusConfig';

interface EvaluationRunStatusBadgeProps {
  status: EvaluationRunStatus;
  className?: string;
}

export function EvaluationRunStatusBadge({ status, className }: EvaluationRunStatusBadgeProps) {
  return <StatusBadge status={status} config={RUN_STATUS_BADGE_CONFIG} className={className} />;
}
