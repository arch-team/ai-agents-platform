import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import type { Agent } from '@/entities/agent';
import { Button, Spinner, ErrorMessage } from '@/shared/ui';

import { useAgent, useUpdateAgent } from '../api/queries';
import { updateAgentSchema } from '../lib/validation';

import { AgentFormFields } from './AgentFormFields';

import type { UpdateAgentFormData } from '../lib/validation';

interface AgentEditFormProps {
  agentId: number;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function AgentEditForm({ agentId, onSuccess, onCancel }: AgentEditFormProps) {
  const { data: agent, isLoading, error } = useAgent(agentId);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !agent) {
    return <ErrorMessage error={error instanceof Error ? error.message : '加载 Agent 失败'} />;
  }

  return <AgentEditFormInner agent={agent} onSuccess={onSuccess} onCancel={onCancel} />;
}

// 内部表单组件，仅在 agent 数据就绪后渲染
interface AgentEditFormInnerProps {
  agent: Agent;
  onSuccess?: () => void;
  onCancel?: () => void;
}

function AgentEditFormInner({ agent, onSuccess, onCancel }: AgentEditFormInnerProps) {
  const updateMutation = useUpdateAgent();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UpdateAgentFormData>({
    resolver: zodResolver(updateAgentSchema),
    defaultValues: {
      name: agent.name,
      description: agent.description,
      system_prompt: agent.system_prompt,
      model_id: agent.config.model_id,
      temperature: agent.config.temperature,
      max_tokens: agent.config.max_tokens,
    },
  });

  const handleFormSubmit = async (data: UpdateAgentFormData) => {
    try {
      await updateMutation.mutateAsync({ id: agent.id, ...data });
      onSuccess?.();
    } catch {
      // 错误由 updateMutation.isError 处理，UI 中展示
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6" noValidate>
      <AgentFormFields register={register} errors={errors} />

      {/* 提交错误提示 */}
      {updateMutation.isError && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {updateMutation.error instanceof Error
            ? updateMutation.error.message
            : '更新失败，请重试'}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex items-center justify-end gap-3">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            取消
          </Button>
        )}
        <Button type="submit" loading={isSubmitting || updateMutation.isPending}>
          保存修改
        </Button>
      </div>
    </form>
  );
}
