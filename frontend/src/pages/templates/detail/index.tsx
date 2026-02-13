// 模板详情页面
import { useNavigate, useParams } from 'react-router-dom';

import { TemplateDetail } from '@/features/templates';
import { Spinner } from '@/shared/ui';

export default function TemplateDetailPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();
  const id = templateId ? Number(templateId) : undefined;

  if (!id) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <TemplateDetail
        templateId={id}
        onBack={() => navigate('/templates')}
      />
    </div>
  );
}
