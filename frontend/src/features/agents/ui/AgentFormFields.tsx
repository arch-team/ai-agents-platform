// Agent 表单共享字段 — 被 AgentCreateForm 和 AgentEditForm 复用

import { useState } from 'react';

import { Input, Textarea } from '@/shared/ui';

import { MODEL_OPTIONS } from '../model/constants';

import type { FieldErrors, UseFormRegister, UseFormWatch } from 'react-hook-form';

import type { CreateAgentFormData } from '../lib/validation';

/** 系统提示词最大字符数 */
const SYSTEM_PROMPT_MAX_LENGTH = 10000;

interface AgentFormFieldsProps {
  register: UseFormRegister<CreateAgentFormData>;
  errors: FieldErrors<CreateAgentFormData>;
  watch: UseFormWatch<CreateAgentFormData>;
}

export function AgentFormFields({ register, errors, watch }: AgentFormFieldsProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const systemPromptValue = watch('system_prompt') ?? '';
  const temperatureValue = watch('temperature') ?? 0.7;

  return (
    <>
      {/* 名称 */}
      <Input
        label="名称"
        placeholder="输入 Agent 名称"
        error={errors.name?.message}
        required
        aria-required="true"
        {...register('name')}
      />

      {/* 描述 */}
      <Textarea
        label="描述"
        placeholder="描述这个 Agent 的用途"
        rows={3}
        error={errors.description?.message}
        {...register('description')}
      />

      {/* 系统提示词 + 字符计数 */}
      <div>
        <Textarea
          label="系统提示词"
          placeholder="输入系统提示词，定义 Agent 的行为和角色"
          rows={6}
          error={errors.system_prompt?.message}
          {...register('system_prompt')}
        />
        <p className="mt-1 text-right text-xs text-gray-400" aria-live="polite">
          {systemPromptValue.length.toLocaleString()} / {SYSTEM_PROMPT_MAX_LENGTH.toLocaleString()}
        </p>
      </div>

      {/* 高级选项折叠区 */}
      <div>
        <button
          type="button"
          className="flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-gray-900"
          onClick={() => setShowAdvanced(!showAdvanced)}
          aria-expanded={showAdvanced}
          aria-controls="advanced-options"
        >
          <span className={`transition-transform ${showAdvanced ? 'rotate-90' : ''}`}>&#9654;</span>
          模型配置（高级选项）
        </button>

        {showAdvanced && (
          <div
            id="advanced-options"
            className="mt-4 space-y-4 rounded-md border border-gray-200 p-4"
          >
            {/* 模型选择 + 成本对比说明 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="model_id" className="text-sm font-medium text-gray-700">
                模型
              </label>
              <select
                id="model_id"
                className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                {...register('model_id')}
              >
                {MODEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500">
                Haiku: 最经济 ($0.25/百万输入) | Sonnet: 均衡 ($3/百万输入) | Opus: 最强 ($15/百万输入)
              </p>
            </div>

            {/* 温度滑块 + 说明 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="temperature" className="text-sm font-medium text-gray-700">
                温度: {temperatureValue}
              </label>
              <input
                id="temperature"
                type="range"
                min="0"
                max="1"
                step="0.1"
                className="w-full"
                aria-invalid={errors.temperature ? true : undefined}
                aria-describedby={
                  errors.temperature ? 'temperature-error' : 'temperature-hint'
                }
                {...register('temperature', { valueAsNumber: true })}
              />
              {errors.temperature && (
                <span id="temperature-error" role="alert" className="text-sm text-red-600">
                  {errors.temperature.message}
                </span>
              )}
              <p id="temperature-hint" className="text-xs text-gray-500">
                低温度 (0-0.3): 精确、一致 | 中温度 (0.4-0.7): 均衡 | 高温度 (0.8-1.0): 创意、多样
              </p>
            </div>

            {/* 最大 Token 数 */}
            <Input
              label="最大 Token 数 (Max Tokens)"
              type="number"
              min={1}
              max={4096}
              error={errors.max_tokens?.message}
              {...register('max_tokens', { valueAsNumber: true })}
            />
          </div>
        )}
      </div>
    </>
  );
}
