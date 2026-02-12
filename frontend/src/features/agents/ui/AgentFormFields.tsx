// Agent 表单共享字段 — 被 AgentCreateForm 和 AgentEditForm 复用

import { useState } from 'react';

import { Input, Textarea } from '@/shared/ui';

import { MODEL_OPTIONS } from '../model/constants';

import type { FieldErrors, UseFormRegister } from 'react-hook-form';
import type { CreateAgentFormData } from '../lib/validation';

interface AgentFormFieldsProps {
  register: UseFormRegister<CreateAgentFormData>;
  errors: FieldErrors<CreateAgentFormData>;
}

export function AgentFormFields({ register, errors }: AgentFormFieldsProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

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

      {/* 系统提示词 */}
      <Textarea
        label="系统提示词"
        placeholder="输入系统提示词，定义 Agent 的行为和角色"
        rows={6}
        error={errors.system_prompt?.message}
        {...register('system_prompt')}
      />

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
            {/* 模型选择 */}
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
            </div>

            {/* 温度滑块 */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="temperature" className="text-sm font-medium text-gray-700">
                温度 (Temperature)
              </label>
              <input
                id="temperature"
                type="range"
                min="0"
                max="1"
                step="0.1"
                className="w-full"
                aria-invalid={errors.temperature ? true : undefined}
                aria-describedby={errors.temperature ? 'temperature-error' : undefined}
                {...register('temperature', { valueAsNumber: true })}
              />
              {errors.temperature && (
                <span id="temperature-error" role="alert" className="text-sm text-red-600">
                  {errors.temperature.message}
                </span>
              )}
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
