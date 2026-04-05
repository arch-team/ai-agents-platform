// Builder 右侧面板 — Blueprint 业务能力预览
// 六大能力区块: 角色 / 技能 / 工具 / 知识库 / 记忆 / 护栏

import { useBuilderBlueprint, useBuilderIsGenerating, useBuilderPhase } from '../model/store';

import { SkillCard } from './SkillCard';

export function BuilderPreview() {
  const blueprint = useBuilderBlueprint();
  const isGenerating = useBuilderIsGenerating();
  const phase = useBuilderPhase();

  // 空状态
  if (!blueprint) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center text-gray-400">
        {isGenerating ? (
          <>
            <div className="mb-3 h-10 w-10 animate-pulse rounded-full bg-blue-100" />
            <p className="text-sm">正在生成 Agent 蓝图，请稍候…</p>
          </>
        ) : (
          <>
            <div className="mb-3 text-3xl">📋</div>
            <p className="text-sm">描述你的 Agent 需求后，蓝图将在此处预览</p>
            <p className="mt-1 text-xs">包含角色定义、技能列表、工具绑定、知识库、记忆和护栏配置</p>
          </>
        )}
      </div>
    );
  }

  const isReadOnly = phase === 'testing';

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          {isReadOnly ? 'Agent 蓝图（只读）' : 'Agent 蓝图预览'}
        </h2>
        {isGenerating && <span className="text-xs text-blue-500">更新中…</span>}
      </div>

      <div className="space-y-4">
        {/* 👤 角色定义 */}
        {blueprint.persona && (
          <section className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
              <span aria-hidden="true">👤</span> 角色定义
            </h3>
            <div className="space-y-1.5">
              <p className="text-sm text-gray-800">
                <span className="font-medium text-gray-500">角色: </span>
                {blueprint.persona.role}
              </p>
              <p className="text-sm text-gray-800">
                <span className="font-medium text-gray-500">背景: </span>
                {blueprint.persona.background}
              </p>
              {blueprint.persona.tone && (
                <p className="text-sm text-gray-800">
                  <span className="font-medium text-gray-500">语气: </span>
                  {blueprint.persona.tone}
                </p>
              )}
            </div>
          </section>
        )}

        {/* 📋 技能列表 */}
        {blueprint.skills.length > 0 && (
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
              <span aria-hidden="true">📋</span> 技能（{blueprint.skills.length}）
            </h3>
            <div className="space-y-2">
              {blueprint.skills.map((skill, i) => (
                <SkillCard key={i} skill={skill} />
              ))}
            </div>
          </section>
        )}

        {/* 🔧 工具绑定 */}
        {blueprint.tool_bindings.length > 0 && (
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
              <span aria-hidden="true">🔧</span> 工具绑定（{blueprint.tool_bindings.length}）
            </h3>
            <div className="space-y-1.5">
              {blueprint.tool_bindings.map((tool) => (
                <div
                  key={tool.tool_id}
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2"
                >
                  <p className="text-sm font-medium text-gray-900">{tool.display_name}</p>
                  {tool.usage_hint && (
                    <p className="mt-0.5 text-xs text-gray-500">{tool.usage_hint}</p>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 📚 知识库 */}
        {blueprint.knowledge_base_ids.length > 0 && (
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
              <span aria-hidden="true">📚</span> 知识库（{blueprint.knowledge_base_ids.length}）
            </h3>
            <div className="flex flex-wrap gap-2">
              {blueprint.knowledge_base_ids.map((id) => (
                <span
                  key={id}
                  className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700"
                >
                  KB-{id}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* 🧠 记忆配置 */}
        {blueprint.memory_config && (
          <section className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
              <span aria-hidden="true">🧠</span> 记忆
            </h3>
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                  blueprint.memory_config.enabled
                    ? 'bg-green-50 text-green-700'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {blueprint.memory_config.enabled ? '已启用' : '未启用'}
              </span>
              {blueprint.memory_config.enabled && (
                <span className="text-xs text-gray-500">
                  策略: {blueprint.memory_config.strategy}
                </span>
              )}
            </div>
            {blueprint.memory_config.enabled &&
              blueprint.memory_config.retain_fields.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {blueprint.memory_config.retain_fields.map((field) => (
                    <span
                      key={field}
                      className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
                    >
                      {field}
                    </span>
                  ))}
                </div>
              )}
          </section>
        )}

        {/* 🛡️ 护栏规则 */}
        {blueprint.guardrails.length > 0 && (
          <section>
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900">
              <span aria-hidden="true">🛡️</span> 护栏规则（{blueprint.guardrails.length}）
            </h3>
            <div className="space-y-1.5">
              {blueprint.guardrails.map((guard, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2"
                >
                  <span
                    className={`mt-0.5 inline-flex flex-shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${
                      guard.severity === 'block'
                        ? 'bg-red-50 text-red-700'
                        : 'bg-yellow-50 text-yellow-700'
                    }`}
                  >
                    {guard.severity === 'block' ? '阻断' : '警告'}
                  </span>
                  <p className="text-sm text-gray-800">{guard.rule}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
