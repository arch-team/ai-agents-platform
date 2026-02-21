import { z } from 'zod';

export const createAgentSchema = z.object({
  name: z.string().min(1, '名称不能为空').max(100, '名称不能超过 100 个字符'),
  description: z.string().max(500, '描述不能超过 500 个字符').default(''),
  system_prompt: z
    .string()
    .min(1, '系统提示词不能为空（激活 Agent 时必需）')
    .max(10000, '系统提示词不能超过 10000 个字符'),
  model_id: z.string().max(200).optional(),
  temperature: z.number().min(0, '温度最小为 0').max(1, '温度最大为 1').optional(),
  max_tokens: z
    .number()
    .int('最大 Token 数必须为整数')
    .min(1, '最小为 1')
    .max(4096, '最大为 4096')
    .optional(),
});

export type CreateAgentFormData = z.input<typeof createAgentSchema>;
