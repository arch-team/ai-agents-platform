// 工具目录列表页面
import { useNavigate } from 'react-router-dom';

import { ToolList } from '@/features/tool-catalog';

export default function ToolListPage() {
  const navigate = useNavigate();

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">工具目录</h1>
      <ToolList onSelect={(id) => navigate(`/tools/${id}`)} />
    </div>
  );
}
