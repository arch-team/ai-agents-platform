// 模板详情 + 配置预览组件
import { useNavigate } from 'react-router-dom';

import { Button, Card, Spinner, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';

import { useTemplate, usePublishTemplate, useArchiveTemplate } from '../api/queries';

import type { TemplateCategory } from '../api/types';
import { TemplateStatusBadge } from './TemplateStatusBadge';
import { CATEGORY_CONFIG } from './CategoryFilter';

interface TemplateDetailProps {
  templateId: number;
  onBack?: () => void;
}

export function TemplateDetail({ templateId, onBack }: TemplateDetailProps) {
  const navigate = useNavigate();
  const { data: template, isLoading, error } = useTemplate(templateId);

  const publishMutation = usePublishTemplate();
  const archiveMutation = useArchiveTemplate();

  const handleUseTemplate = () => {
    if (!template) return;
    navigate('/agents/create', {
      state: {
        fromTemplate: {
          system_prompt: template.system_prompt,
          model_id: template.model_id,
          temperature: template.temperature,
          max_tokens: template.max_tokens,
        },
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="p-6">
        <ErrorMessage error={extractApiError(error, '加载模板详情失败')} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 操作错误提示 */}
      {publishMutation.isError && (
        <ErrorMessage error={extractApiError(publishMutation.error, '发布模板失败')} />
      )}
      {archiveMutation.isError && (
        <ErrorMessage error={extractApiError(archiveMutation.error, '归档模板失败')} />
      )}

      {/* 标题和操作 */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{template.name}</h1>
            <TemplateStatusBadge status={template.status} />
          </div>
          {template.description && <p className="mt-2 text-gray-600">{template.description}</p>}
        </div>
        <div className="flex gap-2">
          {template.status === 'draft' && (
            <Button
              variant="primary"
              size="sm"
              loading={publishMutation.isPending}
              onClick={() => publishMutation.mutate(template.id)}
              aria-label={`发布 ${template.name}`}
            >
              发布
            </Button>
          )}
          {template.status === 'published' && (
            <>
              <Button
                variant="primary"
                size="sm"
                onClick={handleUseTemplate}
                aria-label={`使用 ${template.name} 模板创建 Agent`}
              >
                使用此模板
              </Button>
              <Button
                variant="outline"
                size="sm"
                loading={archiveMutation.isPending}
                onClick={() => archiveMutation.mutate(template.id)}
                aria-label={`归档 ${template.name}`}
              >
                归档
              </Button>
            </>
          )}
          {onBack && (
            <Button variant="outline" size="sm" onClick={onBack}>
              返回列表
            </Button>
          )}
        </div>
      </div>

      {/* 基本信息 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">基本信息</h2>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">分类</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {CATEGORY_CONFIG[template.category as TemplateCategory]?.label ?? template.category}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">创建者 ID</dt>
            <dd className="mt-1 text-sm text-gray-900">{template.creator_id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">使用次数</dt>
            <dd className="mt-1 text-sm text-gray-900">{template.usage_count} 次</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">创建时间</dt>
            <dd className="mt-1 text-sm text-gray-900">{formatDateTime(template.created_at)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">更新时间</dt>
            <dd className="mt-1 text-sm text-gray-900">{formatDateTime(template.updated_at)}</dd>
          </div>
        </dl>
      </Card>

      {/* 系统提示词 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">系统提示词</h2>
        <div className="whitespace-pre-wrap rounded-md bg-gray-50 p-4 text-sm text-gray-700">
          {template.system_prompt}
        </div>
      </Card>

      {/* 配置预览 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">配置预览</h2>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">模型</dt>
            <dd className="mt-1 text-sm text-gray-900">{template.model_id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">温度</dt>
            <dd className="mt-1 text-sm text-gray-900">{template.temperature}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">最大 Token 数</dt>
            <dd className="mt-1 text-sm text-gray-900">{template.max_tokens}</dd>
          </div>
          {template.tool_ids && template.tool_ids.length > 0 && (
            <div>
              <dt className="text-sm font-medium text-gray-500">工具</dt>
              <dd className="mt-1 flex flex-wrap gap-1">
                {template.tool_ids.map((toolId) => (
                  <span
                    key={toolId}
                    className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                  >
                    {toolId}
                  </span>
                ))}
              </dd>
            </div>
          )}
          {template.knowledge_base_ids && template.knowledge_base_ids.length > 0 && (
            <div>
              <dt className="text-sm font-medium text-gray-500">关联知识库</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {template.knowledge_base_ids.join(', ')}
              </dd>
            </div>
          )}
        </dl>
      </Card>
    </div>
  );
}
