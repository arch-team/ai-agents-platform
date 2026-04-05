// Agent 创建页面 — 统一跳转 Builder (V1 AgentCreateForm 已移除)
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AgentCreatePage() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate('/builder', { replace: true });
  }, [navigate]);

  return null;
}
