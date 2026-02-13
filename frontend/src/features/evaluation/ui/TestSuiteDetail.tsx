// 测试集详情 + 用例管理组件

import { useState } from 'react';

import { extractApiError } from '@/shared/lib/extractApiError';
import { formatDateTime } from '@/shared/lib/formatDate';
import { Button, Card, Spinner, ErrorMessage } from '@/shared/ui';

import {
  useTestSuite,
  useTestCases,
  useDeleteTestCase,
  useActivateTestSuite,
  useArchiveTestSuite,
} from '../api/queries';
import type { TestSuiteStatus, TestCase } from '../api/types';

import { TestCaseForm } from './TestCaseForm';
import { TestSuiteStatusBadge } from './TestSuiteStatusBadge';

interface TestSuiteDetailProps {
  suiteId: number;
  onBack?: () => void;
  onRunEvaluation?: (suiteId: number) => void;
}

export function TestSuiteDetail({ suiteId, onBack, onRunEvaluation }: TestSuiteDetailProps) {
  const { data: suite, isLoading, error } = useTestSuite(suiteId);
  const { data: casesData, isLoading: casesLoading } = useTestCases(suiteId);
  const deleteCaseMutation = useDeleteTestCase();
  const activateMutation = useActivateTestSuite();
  const archiveMutation = useArchiveTestSuite();
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !suite) {
    return (
      <div className="p-6">
        <ErrorMessage error={extractApiError(error, '加载测试集详情失败')} />
      </div>
    );
  }

  const isDraft = suite.status === 'draft';
  const isActive = suite.status === 'active';

  return (
    <div className="space-y-6">
      {/* 操作错误提示 */}
      {activateMutation.isError && (
        <ErrorMessage error={extractApiError(activateMutation.error, '激活测试集失败')} />
      )}
      {archiveMutation.isError && (
        <ErrorMessage error={extractApiError(archiveMutation.error, '归档测试集失败')} />
      )}

      {/* 标题和操作 */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{suite.name}</h1>
            <TestSuiteStatusBadge status={suite.status as TestSuiteStatus} />
          </div>
          {suite.description && <p className="mt-2 text-gray-600">{suite.description}</p>}
          <p className="mt-1 text-sm text-gray-400">
            Agent ID: {suite.agent_id} | 创建于 {formatDateTime(suite.created_at)}
          </p>
        </div>
        <div className="flex gap-2">
          {isDraft && (
            <Button
              variant="primary"
              size="sm"
              loading={activateMutation.isPending}
              onClick={() => activateMutation.mutate(suiteId)}
              aria-label={`激活 ${suite.name}`}
            >
              激活
            </Button>
          )}
          {isActive && (
            <>
              <Button
                variant="primary"
                size="sm"
                onClick={() => onRunEvaluation?.(suiteId)}
                aria-label="发起评估"
              >
                发起评估
              </Button>
              <Button
                variant="outline"
                size="sm"
                loading={archiveMutation.isPending}
                onClick={() => archiveMutation.mutate(suiteId)}
                aria-label={`归档 ${suite.name}`}
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

      {/* 测试用例区域 */}
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            测试用例 ({casesData?.total ?? 0})
          </h2>
          {isDraft && !showAddForm && (
            <Button size="sm" onClick={() => setShowAddForm(true)}>
              添加用例
            </Button>
          )}
        </div>

        {/* 添加用例表单 */}
        {showAddForm && (
          <div className="mb-4">
            <TestCaseForm
              suiteId={suiteId}
              onSuccess={() => setShowAddForm(false)}
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        )}

        {/* 编辑用例表单 */}
        {editingCase && (
          <div className="mb-4">
            <TestCaseForm
              key={editingCase.id}
              suiteId={suiteId}
              editCase={editingCase}
              onSuccess={() => setEditingCase(null)}
              onCancel={() => setEditingCase(null)}
            />
          </div>
        )}

        {/* 用例列表 */}
        {casesLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : !casesData?.items.length ? (
          <p className="py-4 text-sm text-gray-500">暂无测试用例</p>
        ) : (
          <ul className="divide-y divide-gray-100" role="list" aria-label="测试用例列表">
            {casesData.items.map((tc) => (
              <li key={tc.id} className="py-3">
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      #{tc.order_index + 1} 输入提示词
                    </p>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-gray-700">
                      {tc.input_prompt}
                    </p>
                    {tc.expected_output && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-gray-500">期望输出</p>
                        <p className="mt-0.5 whitespace-pre-wrap text-sm text-gray-600">
                          {tc.expected_output}
                        </p>
                      </div>
                    )}
                    {tc.evaluation_criteria && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-gray-500">评分标准</p>
                        <p className="mt-0.5 text-sm text-gray-600">{tc.evaluation_criteria}</p>
                      </div>
                    )}
                  </div>
                  {isDraft && (
                    <div className="ml-4 flex shrink-0 gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingCase(tc)}
                        aria-label={`编辑用例 #${tc.order_index + 1}`}
                      >
                        编辑
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        loading={deleteCaseMutation.isPending}
                        onClick={() =>
                          deleteCaseMutation.mutate({ suiteId, caseId: tc.id })
                        }
                        aria-label={`删除用例 #${tc.order_index + 1}`}
                      >
                        删除
                      </Button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
