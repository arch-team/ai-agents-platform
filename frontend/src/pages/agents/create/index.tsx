// Agent 创建页面
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { AgentCreateForm, type ToolOption } from '@/features/agents';
import { useApprovedTools, TOOL_TYPE_LABELS } from '@/features/tool-catalog';
import { extractApiError } from '@/shared/lib/extractApiError';
import { Card } from '@/shared/ui';

export default function AgentCreatePage() {
  const navigate = useNavigate();

  // 页面层获取已审批工具，转换为 ToolOption 格式后注入 feature 组件
  const { data: toolsData, isLoading: toolsLoading, error: toolsError } = useApprovedTools();
  const tools: ToolOption[] = useMemo(
    () =>
      (toolsData?.items ?? []).map((t) => ({
        id: t.id,
        name: t.name,
        description: t.description,
        typeLabel: TOOL_TYPE_LABELS[t.tool_type] ?? t.tool_type,
      })),
    [toolsData],
  );

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">创建 Agent</h1>
      <Card>
        <AgentCreateForm
          onSuccess={(id) => navigate(`/agents/${id}`)}
          onCancel={() => navigate('/agents')}
          tools={tools}
          toolsLoading={toolsLoading}
          toolsError={toolsError ? extractApiError(toolsError, '工具列表加载失败') : null}
        />
      </Card>
    </div>
  );
}
