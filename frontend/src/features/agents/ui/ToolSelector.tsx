// 工具选择器 — Agent 表单中选择要绑定的已审批工具

import { useApprovedTools, TOOL_TYPE_LABELS, type Tool } from '@/features/tool-catalog';

import { Spinner } from '@/shared/ui';

interface ToolSelectorProps {
  selectedIds: number[];
  onChange: (ids: number[]) => void;
}

export function ToolSelector({ selectedIds, onChange }: ToolSelectorProps) {
  const { data, isLoading, error } = useApprovedTools();
  const tools: Tool[] = data?.items ?? [];

  // 切换选中状态：已选则移除，未选则添加
  const handleToggle = (toolId: number) => {
    const next = selectedIds.includes(toolId)
      ? selectedIds.filter((id) => id !== toolId)
      : [...selectedIds, toolId];
    onChange(next);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-sm text-gray-500">
        <Spinner /> 加载可用工具...
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-500">工具列表加载失败</p>;
  }

  if (tools.length === 0) {
    return <p className="text-sm text-gray-400">暂无已审批工具，请先在工具目录中注册并审批工具</p>;
  }

  return (
    <fieldset>
      <legend className="text-sm font-medium text-gray-700">
        绑定工具{' '}
        <span className="font-normal text-gray-400">
          ({selectedIds.length}/{tools.length} 已选)
        </span>
      </legend>

      <div
        role="group"
        aria-label="工具选择"
        className="mt-2 max-h-64 space-y-2 overflow-y-auto rounded-md border border-gray-200 p-3"
      >
        {tools.map((tool) => {
          const checked = selectedIds.includes(Number(tool.id));
          const checkboxId = `tool-${tool.id}`;
          return (
            <label
              key={tool.id}
              htmlFor={checkboxId}
              className={`flex cursor-pointer items-start gap-3 rounded-md border p-3 transition-colors ${
                checked
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-gray-100 bg-white hover:border-gray-300'
              }`}
            >
              <input
                id={checkboxId}
                type="checkbox"
                checked={checked}
                onChange={() => handleToggle(Number(tool.id))}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">{tool.name}</span>
                  <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                    {TOOL_TYPE_LABELS[tool.tool_type] ?? tool.tool_type}
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
    </fieldset>
  );
}
