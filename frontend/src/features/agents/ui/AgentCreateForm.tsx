import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { Button, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useCreateAgent } from '../api/queries';
import { createAgentSchema, type CreateAgentFormData } from '../lib/validation';

import { AgentFormFields } from './AgentFormFields';

interface AgentCreateFormProps {
  onSuccess?: (id: number) => void;
  onCancel?: () => void;
}

export function AgentCreateForm({ onSuccess, onCancel }: AgentCreateFormProps) {
  const createMutation = useCreateAgent();

  const {
    register,
    handleSubmit,
    watch,
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
      <AgentFormFields register={register} errors={errors} watch={watch} />

      {/* 提交错误提示 */}
      {createMutation.isError && (
        <ErrorMessage error={extractApiError(createMutation.error, '创建失败，请重试')} />
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
