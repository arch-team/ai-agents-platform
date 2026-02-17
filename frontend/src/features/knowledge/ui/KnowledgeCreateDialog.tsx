// 创建知识库对话框
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button, Input, Textarea, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useCreateKnowledgeBase } from '../api/queries';

const createKnowledgeBaseSchema = z.object({
  name: z.string().min(1, '名称不能为空').max(100, '名称不能超过 100 个字符'),
  description: z.string().max(500, '描述不能超过 500 个字符'),
});

type CreateKnowledgeBaseFormData = z.infer<typeof createKnowledgeBaseSchema>;

interface KnowledgeCreateDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (id: number) => void;
}

export function KnowledgeCreateDialog({ open, onClose, onSuccess }: KnowledgeCreateDialogProps) {
  const createMutation = useCreateKnowledgeBase();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateKnowledgeBaseFormData>({
    resolver: zodResolver(createKnowledgeBaseSchema),
    defaultValues: { name: '', description: '' },
  });

  const handleFormSubmit = async (data: CreateKnowledgeBaseFormData) => {
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
      aria-labelledby="create-kb-title"
    >
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 id="create-kb-title" className="mb-4 text-lg font-semibold text-gray-900">
          创建知识库
        </h2>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4" noValidate>
          <Input
            label="名称"
            placeholder="输入知识库名称"
            error={errors.name?.message}
            {...register('name')}
          />

          <Textarea
            label="描述"
            placeholder="输入知识库描述（可选）"
            rows={3}
            error={errors.description?.message}
            {...register('description')}
          />

          {createMutation.isError && (
            <ErrorMessage error={extractApiError(createMutation.error, '创建知识库失败')} />
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
