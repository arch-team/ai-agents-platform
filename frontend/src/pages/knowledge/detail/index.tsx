// 知识库详情页面
import { useNavigate, useParams } from 'react-router-dom';

import { KnowledgeDetail } from '@/features/knowledge';
import { Spinner } from '@/shared/ui';

export default function KnowledgeDetailPage() {
  const { knowledgeBaseId } = useParams<{ knowledgeBaseId: string }>();
  const navigate = useNavigate();
  const id = knowledgeBaseId ? Number(knowledgeBaseId) : undefined;

  if (!id) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <KnowledgeDetail
        knowledgeBaseId={id}
        onBack={() => navigate('/knowledge')}
      />
    </div>
  );
}
