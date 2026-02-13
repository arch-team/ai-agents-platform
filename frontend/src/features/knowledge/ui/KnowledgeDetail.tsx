// 知识库详情 + 文档管理组件
import { useState } from 'react';

import { Button, Card, Spinner, ErrorMessage } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';
import { formatFileSize } from '@/shared/lib/formatFileSize';

import {
  useKnowledgeBase,
  useKnowledgeDocuments,
  useDeleteDocument,
  useSyncKnowledgeBase,
  useQueryKnowledgeBase,
} from '../api/queries';

import { KnowledgeStatusBadge } from './KnowledgeStatusBadge';
import { DocumentUpload } from './DocumentUpload';

interface KnowledgeDetailProps {
  knowledgeBaseId: number;
  onBack?: () => void;
}

export function KnowledgeDetail({ knowledgeBaseId, onBack }: KnowledgeDetailProps) {
  const { data: kb, isLoading, error } = useKnowledgeBase(knowledgeBaseId);
  const { data: docsData, isLoading: docsLoading } = useKnowledgeDocuments(knowledgeBaseId);

  const deleteMutation = useDeleteDocument();
  const syncMutation = useSyncKnowledgeBase();
  const queryMutation = useQueryKnowledgeBase();

  const [queryText, setQueryText] = useState('');

  const handleDeleteDoc = (docId: number) => {
    deleteMutation.mutate({ kbId: knowledgeBaseId, docId });
  };

  const handleSync = () => {
    syncMutation.mutate(knowledgeBaseId);
  };

  const handleQuery = (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;
    queryMutation.mutate({ id: knowledgeBaseId, query: queryText });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !kb) {
    return (
      <div className="p-6">
        <ErrorMessage error={extractApiError(error, '加载知识库详情失败')} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题和操作 */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{kb.name}</h1>
            <KnowledgeStatusBadge status={kb.status} />
          </div>
          {kb.description && <p className="mt-2 text-gray-600">{kb.description}</p>}
        </div>
        <div className="flex gap-2">
          {kb.status === 'ACTIVE' && (
            <Button
              variant="outline"
              size="sm"
              loading={syncMutation.isPending}
              onClick={handleSync}
              aria-label="同步知识库"
            >
              同步
            </Button>
          )}
          {onBack && (
            <Button variant="outline" size="sm" onClick={onBack}>
              返回列表
            </Button>
          )}
        </div>
      </div>

      {/* 同步操作错误提示 */}
      {syncMutation.isError && (
        <ErrorMessage error={extractApiError(syncMutation.error, '同步知识库失败')} />
      )}

      {/* 基本信息 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">基本信息</h2>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">文档数量</dt>
            <dd className="mt-1 text-sm text-gray-900">{kb.document_count} 个</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">创建时间</dt>
            <dd className="mt-1 text-sm text-gray-900">{formatDateTime(kb.created_at)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">更新时间</dt>
            <dd className="mt-1 text-sm text-gray-900">{formatDateTime(kb.updated_at)}</dd>
          </div>
        </dl>
      </Card>

      {/* 文档管理 */}
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">文档管理</h2>
        </div>

        {/* 上传 */}
        <div className="mb-4 border-b border-gray-100 pb-4">
          <DocumentUpload knowledgeBaseId={knowledgeBaseId} />
        </div>

        {/* 文档列表 */}
        {docsLoading ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : !docsData?.items.length ? (
          <p className="text-sm text-gray-500">暂无文档，请上传文档</p>
        ) : (
          <ul className="divide-y divide-gray-100" role="list" aria-label="文档列表">
            {docsData.items.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{doc.file_name}</p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(doc.file_size)} · {doc.content_type} · {formatDateTime(doc.created_at)}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  loading={deleteMutation.isPending}
                  onClick={() => handleDeleteDoc(doc.id)}
                  aria-label={`删除文档 ${doc.file_name}`}
                >
                  删除
                </Button>
              </li>
            ))}
          </ul>
        )}

        {/* 删除文档错误提示 */}
        {deleteMutation.isError && (
          <div className="mt-2">
            <ErrorMessage error={extractApiError(deleteMutation.error, '删除文档失败')} />
          </div>
        )}
      </Card>

      {/* RAG 检索 */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">知识检索</h2>
        <form onSubmit={handleQuery} className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="输入检索问题..."
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              aria-label="检索问题"
            />
            <Button
              type="submit"
              size="sm"
              loading={queryMutation.isPending}
              disabled={!queryText.trim()}
            >
              检索
            </Button>
          </div>
        </form>

        {queryMutation.isError && (
          <div className="mt-3">
            <ErrorMessage error={extractApiError(queryMutation.error, '检索失败')} />
          </div>
        )}

        {queryMutation.data && (
          <div className="mt-4 space-y-3">
            <h3 className="text-sm font-medium text-gray-700">
              检索结果 ({queryMutation.data.results.length} 条)
            </h3>
            {queryMutation.data.results.length === 0 ? (
              <p className="text-sm text-gray-500">未找到相关内容</p>
            ) : (
              <ul className="space-y-2" role="list" aria-label="检索结果">
                {queryMutation.data.results.map((result, index) => (
                  <li
                    key={index}
                    className="rounded-md border border-gray-200 bg-gray-50 p-3"
                  >
                    <p className="whitespace-pre-wrap text-sm text-gray-800">{result.content}</p>
                    <p className="mt-1 text-xs text-gray-500">
                      相关度: {(result.score * 100).toFixed(1)}%
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
