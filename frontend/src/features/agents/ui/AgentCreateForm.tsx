import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { Button } from '@/shared/ui';

import { useCreateAgent } from '../api/queries';
import { createAgentSchema } from '../lib/validation';

import { AgentFormFields } from './AgentFormFields';

import type { CreateAgentFormData } from '../lib/validation';

interface AgentCreateFormProps {
  onSuccess?: (id: number) => void;
  onCancel?: () => void;
}

export function AgentCreateForm({ onSuccess, onCancel }: AgentCreateFormProps) {
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
      <AgentFormFields register={register} errors={errors} />

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
