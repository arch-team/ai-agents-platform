// 工具选择器 — Agent 表单中选择要绑定的已审批工具
// 通过 props 注入工具数据，避免跨 feature 依赖（FSD 架构合规）

import { Spinner } from '@/shared/ui';

/** 工具选择器所需的最小工具信息 */
interface ToolOption {
  id: string | number;
  name: string;
  description?: string;
  /** 工具类型显示标签 */
  typeLabel: string;
}

interface ToolSelectorProps {
  selectedIds: number[];
  onChange: (ids: number[]) => void;
  /** 可选工具列表（由调用方注入，避免跨 feature 依赖） */
  tools: ToolOption[];
  /** 数据加载中 */
  isLoading?: boolean;
  /** 数据加载错误 */
  error?: string | null;
}

export type { ToolOption };

export function ToolSelector({
  selectedIds,
  onChange,
  tools,
  isLoading,
  error,
}: ToolSelectorProps) {
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
                    {tool.typeLabel}
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
