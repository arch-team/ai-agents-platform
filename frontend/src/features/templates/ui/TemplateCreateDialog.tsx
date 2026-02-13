// 创建模板对话框
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button, Input, Textarea, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useCreateTemplate } from '../api/queries';
import type { TemplateCategory } from '../api/types';

import { CATEGORY_CONFIG } from './CategoryFilter';

const CATEGORY_OPTIONS = Object.entries(CATEGORY_CONFIG) as Array<
  [TemplateCategory, { label: string }]
>;

const createTemplateSchema = z.object({
  name: z.string().min(1, '名称不能为空').max(100, '名称不能超过 100 个字符'),
  description: z.string().max(500, '描述不能超过 500 个字符').default(''),
  category: z.enum([
    'customer_service',
    'data_analysis',
    'content_creation',
    'code_assistant',
    'research',
    'automation',
    'other',
  ] as const, { required_error: '请选择分类' }),
  system_prompt: z
    .string()
    .min(1, '系统提示词不能为空')
    .max(10000, '系统提示词不能超过 10000 个字符'),
});

type CreateTemplateFormData = z.infer<typeof createTemplateSchema>;

interface TemplateCreateDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (id: number) => void;
}

export function TemplateCreateDialog({ open, onClose, onSuccess }: TemplateCreateDialogProps) {
  const createMutation = useCreateTemplate();

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<CreateTemplateFormData>({
    resolver: zodResolver(createTemplateSchema),
    defaultValues: {
      name: '',
      description: '',
      category: 'other',
      system_prompt: '',
    },
  });

  const handleFormSubmit = async (data: CreateTemplateFormData) => {
    try {
      const result = await createMutation.mutateAsync(data);
      reset();
      onSuccess?.(result.id);
      onClose();
    } catch {
      // 错误由 mutation 状态处理
    }
  };

  const handleCancel = () => {
    reset();
    createMutation.reset();
    onClose();
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-template-title"
    >
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h2 id="create-template-title" className="mb-4 text-lg font-semibold text-gray-900">
          创建模板
        </h2>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4" noValidate>
          <Input
            label="名称"
            placeholder="输入模板名称"
            error={errors.name?.message}
            {...register('name')}
          />

          <Textarea
            label="描述"
            placeholder="输入模板描述（可选）"
            rows={2}
            error={errors.description?.message}
            {...register('description')}
          />

          <Controller
            name="category"
            control={control}
            render={({ field }) => (
              <div className="flex flex-col gap-1.5">
                <label htmlFor="template-category" className="text-sm font-medium text-gray-700">
                  分类
                </label>
                <select
                  id="template-category"
                  value={field.value}
                  onChange={field.onChange}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  aria-invalid={!!errors.category}
                >
                  {CATEGORY_OPTIONS.map(([value, config]) => (
                    <option key={value} value={value}>
                      {config.label}
                    </option>
                  ))}
                </select>
                {errors.category && (
                  <span role="alert" className="text-sm text-red-600">
                    {errors.category.message}
                  </span>
                )}
              </div>
            )}
          />

          <Textarea
            label="系统提示词"
            placeholder="输入系统提示词..."
            rows={4}
            error={errors.system_prompt?.message}
            {...register('system_prompt')}
          />

          {createMutation.isError && (
            <ErrorMessage error={extractApiError(createMutation.error, '创建模板失败')} />
          )}

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={handleCancel}>
              取消
            </Button>
            <Button type="submit" loading={isSubmitting || createMutation.isPending}>
              创建
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
