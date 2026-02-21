// Pipeline 状态徽章组件
import { StatusBadge } from '@/shared/ui';

import type { PipelineStatus } from '../api/types';

import { PIPELINE_STATUS_BADGE_CONFIG } from './pipelineStatusConfig';

interface PipelineStatusBadgeProps {
  status: PipelineStatus;
  className?: string;
}

export function PipelineStatusBadge({ status, className }: PipelineStatusBadgeProps) {
  return (
    <StatusBadge status={status} config={PIPELINE_STATUS_BADGE_CONFIG} className={className} />
  );
}
