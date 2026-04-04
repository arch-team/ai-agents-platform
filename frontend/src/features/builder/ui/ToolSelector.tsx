// Builder 工具选择器 — 在蓝图预览面板中选择/调整绑定的工具
// 复用 agents 模块的 ToolSelector 视觉模式，但面向 Builder 场景：
// - 数据来源是 useAvailableTools() 而非 approved tools
// - 选中状态通过 configOverrides 管理

import { Spinner } from '@/shared/ui';

import type { AvailableToolResponse } from '../api/types';

interface BuilderToolSelectorProps {
  tools: AvailableToolResponse[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
  isLoading?: boolean;
  error?: string | null;
}

export function BuilderToolSelector({
  tools,
  selectedIds,
  onChange,
  isLoading,
  error,
}: BuilderToolSelectorProps) {
  const handleToggle = (toolId: number) => {
    const next = selectedIds.includes(toolId)
      ? selectedIds.filter((id) => id !== toolId)
      : [...selectedIds, toolId];
    onChange(next);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-2 text-sm text-gray-500">
        <Spinner /> 加载可用工具...
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-500">工具列表加载失败</p>;
  }

  if (tools.length === 0) {
    return <p className="text-sm text-gray-400">暂无可用工具</p>;
  }

  return (
    <div role="group" aria-label="工具选择" className="max-h-48 space-y-1.5 overflow-y-auto">
      {tools.map((tool) => {
        const checked = selectedIds.includes(tool.id);
        const checkboxId = `builder-tool-${tool.id}`;
        return (
          <label
            key={tool.id}
            htmlFor={checkboxId}
            className={`flex cursor-pointer items-start gap-2 rounded-lg border p-2 transition-colors ${
              checked
                ? 'border-blue-300 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <input
              id={checkboxId}
              type="checkbox"
              checked={checked}
              onChange={() => handleToggle(tool.id)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-medium text-gray-900">{tool.name}</span>
                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                  {tool.tool_type}
                </span>
              </div>
              {tool.description && (
                <p className="mt-0.5 truncate text-xs text-gray-500">{tool.description}</p>
              )}
            </div>
          </label>
        );
      })}
    </div>
  );
}
