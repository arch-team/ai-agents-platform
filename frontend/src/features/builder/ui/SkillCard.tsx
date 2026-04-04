// SkillCard — 单个 Skill 业务能力展示卡片

import { useState } from 'react';

import type { SkillDefinition } from '../api/types';

interface SkillCardProps {
  skill: SkillDefinition;
}

export function SkillCard({ skill }: SkillCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <button
        type="button"
        className="flex w-full items-start justify-between text-left"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-medium text-gray-900">{skill.name}</h4>
          <p className="mt-0.5 text-xs text-gray-500">{skill.trigger_description}</p>
        </div>
        <span
          className="ml-2 flex-shrink-0 text-gray-400 transition-transform"
          aria-hidden="true"
          style={{ transform: expanded ? 'rotate(180deg)' : undefined }}
        >
          ▾
        </span>
      </button>

      {expanded && (
        <div className="mt-2 space-y-2 border-t border-gray-100 pt-2">
          {skill.steps.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500">执行步骤</p>
              <ol className="mt-1 list-inside list-decimal space-y-0.5 text-xs text-gray-700">
                {skill.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}
          {skill.rules.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500">约束规则</p>
              <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-gray-600">
                {skill.rules.map((rule, i) => (
                  <li key={i}>{rule}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
