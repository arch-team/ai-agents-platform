// 工具注册对话框组件

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button, Input, Textarea } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

import { useCreateTool } from '../api/queries';
import type { ToolType } from '../api/types';

// 工具类型选项
const TOOL_TYPE_OPTIONS: Array<{ value: ToolType; label: string; description: string }> = [
  { value: 'MCP_SERVER', label: 'MCP Server', description: '基于 MCP 协议的工具服务' },
  { value: 'API', label: 'API', description: '外部 REST/GraphQL API 接口' },
  { value: 'FUNCTION', label: 'Function', description: '自定义函数工具' },
];

// 表单验证 schema
const createToolSchema = z.object({
  name: z.string().min(1, '请输入工具名称').max(100, '名称不超过 100 个字符'),
  description: z.string().min(1, '请输入工具描述').max(500, '描述不超过 500 个字符'),
  tool_type: z.enum(['MCP_SERVER', 'API', 'FUNCTION'] as const, {
    required_error: '请选择工具类型',
  }),
  version: z.string().optional(),
});

type CreateToolFormData = z.infer<typeof createToolSchema>;

interface ToolRegisterDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function ToolRegisterDialog({ open, onClose, onSuccess }: ToolRegisterDialogProps) {
  const [apiError, setApiError] = useState<string | null>(null);
  const createMutation = useCreateTool();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateToolFormData>({
    resolver: zodResolver(createToolSchema),
    defaultValues: {
      tool_type: 'MCP_SERVER',
    },
  });

  const handleClose = () => {
    reset();
    setApiError(null);
    onClose();
  };

  const onSubmit = async (data: CreateToolFormData) => {
    setApiError(null);
    try {
      await createMutation.mutateAsync(data);
      handleClose();
      onSuccess?.();
    } catch (error) {
      setApiError(extractApiError(error, '创建工具失败'));
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* 对话框 */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="register-tool-title"
        className="relative z-10 w-full max-w-lg rounded-lg bg-white p-6 shadow-xl"
      >
        <h2 id="register-tool-title" className="mb-4 text-lg font-semibold text-gray-900">
          注册新工具
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="工具名称"
            placeholder="输入工具名称"
            error={errors.name?.message}
            {...register('name')}
          />

          <Textarea
            label="工具描述"
            placeholder="描述工具的功能和用途"
            rows={3}
            error={errors.description?.message}
            {...register('description')}
          />

          {/* 工具类型选择 */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="tool-type" className="text-sm font-medium text-gray-700">
              工具类型
            </label>
            <select
              id="tool-type"
              {...register('tool_type')}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              aria-invalid={errors.tool_type ? true : undefined}
            >
              {TOOL_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label} — {option.description}
                </option>
              ))}
            </select>
            {errors.tool_type && (
              <span role="alert" className="text-sm text-red-600">
                {errors.tool_type.message}
              </span>
            )}
          </div>

          <Input
            label="版本号（可选）"
            placeholder="如: 1.0.0"
            error={errors.version?.message}
            {...register('version')}
          />

          {apiError && (
            <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {apiError}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={handleClose}>
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
