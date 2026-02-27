// Builder 右侧面板 — 实时 Agent 配置预览

import {
  useBuilderGeneratedConfig,
  useBuilderIsGenerating,
  useBuilderActions,
} from '../model/store';

export function BuilderPreview() {
  const config = useBuilderGeneratedConfig();
  const isGenerating = useBuilderIsGenerating();
  const { setGeneratedConfig } = useBuilderActions();

  // 尚无配置时的占位内容
  if (!config) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center text-gray-400">
        {isGenerating ? (
          <>
            <div className="mb-3 h-10 w-10 animate-pulse rounded-full bg-blue-100" />
            <p className="text-sm">正在生成 Agent 配置，请稍候…</p>
          </>
        ) : (
          <>
            <div className="mb-3 h-10 w-10 rounded-full bg-gray-100" />
            <p className="text-sm">生成完成后，Agent 配置将在此处预览</p>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <h2 className="mb-4 text-lg font-semibold text-gray-900">Agent 配置预览</h2>

      <div className="space-y-4">
        {/* Agent 名称（可编辑） */}
        <div>
          <label
            htmlFor="builder-agent-name"
            className="block text-xs font-medium uppercase tracking-wide text-gray-500"
          >
            Agent 名称 <span className="normal-case text-blue-500">（可编辑）</span>
          </label>
          <input
            id="builder-agent-name"
            type="text"
            value={config.name || ''}
            onChange={(e) => setGeneratedConfig({ ...config, name: e.target.value })}
            className="mt-1 w-full rounded-lg border border-blue-300 bg-white px-3 py-2 text-sm text-gray-900
                       focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="输入 Agent 名称"
          />
        </div>

        {/* 描述 */}
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-gray-500">
            描述
          </label>
          <p className="mt-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900">
            {config.description || '（未设置）'}
          </p>
        </div>

        {/* 系统提示词 */}
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-gray-500">
            系统提示词
          </label>
          <div className="mt-1 max-h-40 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
            <pre className="whitespace-pre-wrap font-sans text-sm text-gray-900">
              {config.system_prompt || '（未设置）'}
            </pre>
          </div>
        </div>

        {/* 模型参数 */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium uppercase tracking-wide text-gray-500">
              模型
            </label>
            <p className="mt-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900">
              {config.model_id || '（未设置）'}
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wide text-gray-500">
              温度
            </label>
            <p className="mt-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900">
              {config.temperature ?? '（未设置）'}
            </p>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-gray-500">
            最大 Token 数
          </label>
          <p className="mt-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900">
            {config.max_tokens ?? '（未设置）'}
          </p>
        </div>
      </div>
    </div>
  );
}
