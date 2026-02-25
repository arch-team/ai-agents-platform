// 部门列表 + CRUD 管理

import { useState } from 'react';

import {
  useCreateDepartment,
  useDeleteDepartment,
  useDepartments,
  useUpdateDepartment,
} from '../api/queries';

import type { Department } from '../api/types';

import { Button, Card, ErrorMessage, Input, Spinner } from '@/shared/ui';
import { extractApiError } from '@/shared/lib/extractApiError';

const ACTIVE_BADGE =
  'inline-flex items-center rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700';
const INACTIVE_BADGE =
  'inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500';

interface DepartmentListProps {
  selectedId: number | null;
  onSelect: (dept: Department) => void;
  isAdmin: boolean;
}

export function DepartmentList({ selectedId, onSelect, isAdmin }: DepartmentListProps) {
  const { data, isLoading, error } = useDepartments();
  const createMutation = useCreateDepartment();
  const updateMutation = useUpdateDepartment();
  const deleteMutation = useDeleteDepartment();

  const [showForm, setShowForm] = useState(false);
  const [formName, setFormName] = useState('');
  const [formCode, setFormCode] = useState('');
  const [formDesc, setFormDesc] = useState('');

  if (isLoading)
    return (
      <Card>
        <Spinner />
      </Card>
    );
  if (error) return <ErrorMessage error={extractApiError(error, '加载部门列表失败')} />;

  const departments = data?.items ?? [];

  const handleCreate = async () => {
    if (!formName.trim() || !formCode.trim()) return;
    await createMutation.mutateAsync({ name: formName, code: formCode, description: formDesc });
    setFormName('');
    setFormCode('');
    setFormDesc('');
    setShowForm(false);
  };

  const handleToggleActive = async (dept: Department) => {
    await updateMutation.mutateAsync({ id: dept.id, is_active: !dept.is_active });
  };

  const handleDelete = async (id: number) => {
    await deleteMutation.mutateAsync(id);
  };

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">部门</h3>
        {isAdmin && (
          <Button size="sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? '取消' : '+ 新建'}
          </Button>
        )}
      </div>

      {showForm && (
        <div className="mb-4 space-y-2 rounded-lg border border-blue-100 bg-blue-50 p-3">
          <Input
            placeholder="部门名称"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />
          <Input
            placeholder="部门编码 (英文)"
            value={formCode}
            onChange={(e) => setFormCode(e.target.value)}
          />
          <Input
            placeholder="描述 (可选)"
            value={formDesc}
            onChange={(e) => setFormDesc(e.target.value)}
          />
          <Button size="sm" onClick={handleCreate} disabled={createMutation.isPending}>
            {createMutation.isPending ? '创建中...' : '确认创建'}
          </Button>
        </div>
      )}

      {departments.length === 0 ? (
        <p className="py-4 text-center text-sm text-gray-500">暂无部门</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {departments.map((dept) => (
            <li
              key={dept.id}
              className={`flex cursor-pointer items-center justify-between px-3 py-3 transition-colors hover:bg-gray-50 ${
                selectedId === dept.id ? 'bg-blue-50 ring-1 ring-blue-200' : ''
              }`}
              onClick={() => onSelect(dept)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onSelect(dept)}
              aria-current={selectedId === dept.id ? 'true' : undefined}
            >
              <div>
                <span className="font-medium text-gray-900">{dept.name}</span>
                <span className="ml-2 text-xs text-gray-400">{dept.code}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={dept.is_active ? ACTIVE_BADGE : INACTIVE_BADGE}>
                  {dept.is_active ? '活跃' : '停用'}
                </span>
                {isAdmin && (
                  <>
                    <button
                      className="text-xs text-blue-600 hover:underline"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleActive(dept);
                      }}
                      aria-label={dept.is_active ? `停用 ${dept.name}` : `启用 ${dept.name}`}
                    >
                      {dept.is_active ? '停用' : '启用'}
                    </button>
                    <button
                      className="text-xs text-red-600 hover:underline"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(dept.id);
                      }}
                      aria-label={`删除 ${dept.name}`}
                    >
                      删除
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
