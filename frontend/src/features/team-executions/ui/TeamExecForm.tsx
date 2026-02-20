// 创建 Team Execution 表单

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import type { Agent } from '@/entities/agent';
import { Button, Textarea } from '@/shared/ui';

const teamExecSchema = z.object({
  prompt: z.string().min(1, '请输入执行提示词').max(10000, '提示词不能超过 10000 字符'),
});

type TeamExecFormData = z.infer<typeof teamExecSchema>;

interface TeamExecFormProps {
  agents: Agent[];
  selectedAgentId: number | null;
  onSelectAgent: (id: number) => void;
  onSubmit: (prompt: string) => void;
  isSubmitting: boolean;
}

export function TeamExecForm({
  agents,
  selectedAgentId,
  onSelectAgent,
  onSubmit,
  isSubmitting,
}: TeamExecFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TeamExecFormData>({
    resolver: zodResolver(teamExecSchema),
  });

  // 筛选 active Agent
  const teamAgents = agents.filter((a) => a.status === 'active');

  const handleFormSubmit = (data: TeamExecFormData) => {
    onSubmit(data.prompt);
    reset();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      {/* Agent 选择 */}
      <div>
        <label htmlFor="team-exec-agent" className="mb-1.5 block text-sm font-medium text-gray-700">
          选择 Agent
        </label>
        {teamAgents.length === 0 ? (
          <p className="text-sm text-gray-500">暂无可用的 Agent，请先创建并激活一个 Agent</p>
        ) : (
          <select
            id="team-exec-agent"
            value={selectedAgentId ?? ''}
            onChange={(e) => onSelectAgent(Number(e.target.value))}
            className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="" disabled>
              请选择 Agent
            </option>
            {teamAgents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* 提示词输入 */}
      <Textarea
        label="执行提示词"
        {...register('prompt')}
        placeholder="描述你希望 Agent Team 执行的任务..."
        rows={4}
        error={errors.prompt?.message}
      />

      <Button type="submit" loading={isSubmitting} disabled={!selectedAgentId || isSubmitting}>
        提交执行
      </Button>
    </form>
  );
}
