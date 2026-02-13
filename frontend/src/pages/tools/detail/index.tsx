// 工具详情页面
import { useParams, useNavigate } from 'react-router-dom';

import { ToolDetail } from '@/features/tool-catalog';

export default function ToolDetailPage() {
  const { toolId } = useParams<{ toolId: string }>();
  const navigate = useNavigate();

  if (!toolId) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">无效的工具 ID</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">工具详情</h1>
      <ToolDetail toolId={toolId} onBack={() => navigate('/tools')} />
    </div>
  );
}
