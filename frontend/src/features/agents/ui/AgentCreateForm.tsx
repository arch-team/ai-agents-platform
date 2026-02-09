import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { Button, Input } from '@/shared/ui';

import { useCreateAgent } from '../api/queries';
import { createAgentSchema } from '../lib/validation';

import type { CreateAgentFormData } from '../lib/validation';

// 模型选项
const MODEL_OPTIONS = [
  { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-5-haiku', label: 'Claude 3.5 Haiku' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
];

interface AgentCreateFormProps {
  onSuccess?: (id: number) => void;
  onCancel?: () => void;
}

export function AgentCreateForm({ onSuccess, onCancel }: AgentCreateFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const createMutation = useCreateAgent();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateAgentFormData>({
    resolver: zodResolver(createAgentSchema),
    defaultValues: {
      name: '',
      description: '',
      system_prompt: '',
      model_id: 'claude-3-5-sonnet',
      temperature: 0.7,
      max_tokens: 4096,
    },
  });

  const handleFormSubmit = async (data: CreateAgentFormData) => {
    try {
      const result = await createMutation.mutateAsync(data);
      onSuccess?.(result.id);
    } catch {
      // 错误由 createMutation.isError 处理，UI 中展示
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6" noValidate>
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
      <div className="flex flex-col gap-1.5">
        <label htmlFor="description" className="text-sm font-medium text-gray-700">
          描述
        </label>
        <textarea
          id="description"
          placeholder="描述这个 Agent 的用途"
          rows={3}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          aria-invalid={errors.description ? true : undefined}
          aria-describedby={errors.description ? 'description-error' : undefined}
          {...register('description')}
        />
        {errors.description && (
          <span id="description-error" role="alert" className="text-sm text-red-600">
            {errors.description.message}
          </span>
        )}
      </div>

      {/* 系统提示词 */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="system_prompt" className="text-sm font-medium text-gray-700">
          系统提示词
        </label>
        <textarea
          id="system_prompt"
          placeholder="输入系统提示词，定义 Agent 的行为和角色"
          rows={6}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          aria-invalid={errors.system_prompt ? true : undefined}
          aria-describedby={errors.system_prompt ? 'system-prompt-error' : undefined}
          {...register('system_prompt')}
        />
        {errors.system_prompt && (
          <span id="system-prompt-error" role="alert" className="text-sm text-red-600">
            {errors.system_prompt.message}
          </span>
        )}
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

      {/* 提交错误提示 */}
      {createMutation.isError && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {createMutation.error instanceof Error
            ? createMutation.error.message
            : '创建失败，请重试'}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex items-center justify-end gap-3">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            取消
          </Button>
        )}
        <Button type="submit" loading={isSubmitting || createMutation.isPending}>
          创建 Agent
        </Button>
      </div>
    </form>
  );
}
