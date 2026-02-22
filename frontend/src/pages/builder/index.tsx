// BuilderPage — AI Agent 构建器页面
// 布局：左侧提示词输入 + SSE 消息流 / 右侧 Agent 配置预览 / 底部操作栏

import { useNavigate } from 'react-router-dom';

import { useAuthToken } from '@/features/auth';
import {
  BuilderActions,
  BuilderChat,
  BuilderPreview,
  useBuilderActions,
  useBuilderSessionId,
  useCreateBuilderSession,
  useConfirmBuilderSession,
  useBuilderStream,
} from '@/features/builder';
import { extractApiError } from '@/shared/lib/extractApiError';

export default function BuilderPage() {
  const navigate = useNavigate();
  const token = useAuthToken();

  const sessionId = useBuilderSessionId();
  const { setSessionId, setConfirming, setError, reset } = useBuilderActions();

  const createSession = useCreateBuilderSession();
  const confirmSession = useConfirmBuilderSession();
  const { startGeneration } = useBuilderStream(token);

  /**
   * 用户提交提示词时：
   * 1. 重置状态（支持重新生成）
   * 2. 创建 Builder 会话
   * 3. 启动 SSE 流式生成
   */
  const handleSubmit = async (prompt: string) => {
    reset();
    try {
      const session = await createSession.mutateAsync({ prompt });
      setSessionId(session.id);
      await startGeneration(session.id);
    } catch (err) {
      setError(extractApiError(err, '创建会话失败，请重试'));
    }
  };

  /**
   * 确认创建 Agent：
   * 调用确认接口，成功后跳转到新 Agent 详情页
   */
  const handleConfirm = async (sid: number) => {
    setConfirming(true);
    try {
      const result = await confirmSession.mutateAsync(sid);
      navigate(`/agents/${result.created_agent_id}`);
    } catch (err) {
      setError(extractApiError(err, '创建 Agent 失败，请重试'));
      setConfirming(false);
    }
  };

  /** 取消：重置所有状态，允许重新输入 */
  const handleCancel = () => {
    reset();
  };

  return (
    <div className="flex h-full flex-col">
      {/* 页面标题 */}
      <header className="border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-900">AI Agent 构建器</h1>
        <p className="mt-1 text-sm text-gray-500">描述你需要的 Agent，AI 将自动生成配置</p>
      </header>

      {/* 主体：左右分栏布局 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：提示词输入 + SSE 消息流（5/12） */}
        <div className="w-5/12 border-r border-gray-200 overflow-hidden">
          <BuilderChat hasSession={!!sessionId} onSubmit={(p) => void handleSubmit(p)} />
        </div>

        {/* 右侧：Agent 配置预览（7/12） */}
        <div className="w-7/12 overflow-hidden">
          <BuilderPreview />
        </div>
      </div>

      {/* 底部操作栏 */}
      <BuilderActions onConfirm={(sid) => void handleConfirm(sid)} onCancel={handleCancel} />
    </div>
  );
}
