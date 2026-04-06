// BuilderPage — AI Agent 构建器页面
// 三阶段布局：input → configure → testing
// - input:     全宽起步选择 + 输入区
// - configure: 左5/12对话 + 右7/12蓝图预览
// - testing:   左5/12蓝图摘要(只读) + 右7/12测试沙盒

import { useNavigate } from 'react-router-dom';

import { useAuthToken } from '@/features/auth';
import {
  BuilderActions,
  BuilderChat,
  BuilderPreview,
  TestSandbox,
  useBuilderActions,
  useBuilderCreatedAgentId,
  useBuilderPhase,
  useBuilderSessionId,
  useCreateBuilderSession,
  useConfirmAndTest,
  useGoLive,
  useBlueprintStream,
} from '@/features/builder';
import { extractApiError } from '@/shared/lib/extractApiError';

export default function BuilderPage() {
  const navigate = useNavigate();
  const token = useAuthToken();

  const phase = useBuilderPhase();
  const sessionId = useBuilderSessionId();
  const createdAgentId = useBuilderCreatedAgentId();
  const { setSessionId, setConfirming, setError, setPhase, setCreatedAgentId, addMessage, reset } =
    useBuilderActions();

  const createSession = useCreateBuilderSession();
  const confirmAndTest = useConfirmAndTest();
  const goLive = useGoLive();
  const { startGeneration, startRefinement, abort } = useBlueprintStream(token);

  // 首次提交: 创建会话 → 启动 Blueprint 生成
  const handleSubmitInitial = async (prompt: string) => {
    reset();
    try {
      addMessage({ role: 'user', content: prompt });
      const session = await createSession.mutateAsync({ prompt });
      setSessionId(session.id);
      await startGeneration(session.id);
    } catch (err) {
      setError(extractApiError(err, '创建会话失败，请重试'));
      setPhase('input');
    }
  };

  // 迭代优化: 发送 refine 消息
  const handleSubmitRefine = async (message: string) => {
    if (!sessionId) return;
    try {
      await startRefinement(sessionId, message);
    } catch (err) {
      setError(extractApiError(err, '优化失败，请重试'));
    }
  };

  // 开始测试: confirm(auto_start_testing=true) → 切换到 testing 阶段
  const handleStartTesting = async () => {
    if (!sessionId) return;
    setConfirming(true);
    try {
      const result = await confirmAndTest.mutateAsync({
        sessionId,
        auto_start_testing: true,
      });
      setCreatedAgentId(result.created_agent_id);
      setPhase('testing');
    } catch (err) {
      setError(extractApiError(err, '启动测试失败，请重试'));
    } finally {
      setConfirming(false);
    }
  };

  // 上线发布: go-live → 跳转 Agent 详情页
  const handleGoLive = async () => {
    if (!createdAgentId) return;
    setConfirming(true);
    try {
      await goLive.mutateAsync(createdAgentId);
      navigate(`/agents/${createdAgentId}`);
    } catch (err) {
      setError(extractApiError(err, '上线失败，请重试'));
    } finally {
      setConfirming(false);
    }
  };

  // 返回修改: 从 testing 回到 configure
  const handleBackToEdit = () => {
    setPhase('configure');
  };

  // 取消: 重置所有状态
  const handleCancel = () => {
    abort();
    reset();
  };

  return (
    <div className="flex h-full flex-col">
      {/* 页面标题 */}
      <header className="border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-900">AI Agent 构建器</h1>
        <p className="mt-1 text-sm text-gray-500">
          {phase === 'testing'
            ? '在测试沙盒中验证你的 Agent'
            : '描述你需要的 Agent，AI 将自动生成蓝图'}
        </p>
      </header>

      {/* 主体：三阶段布局 */}
      <div className="flex flex-1 overflow-hidden">
        {phase === 'input' && (
          <div className="flex flex-1 flex-col overflow-hidden">
            <InputPhaseHeader />
            <div className="flex-1 overflow-hidden">
              <BuilderChat
                onSubmitInitial={(p) => void handleSubmitInitial(p)}
                onSubmitRefine={(m) => void handleSubmitRefine(m)}
                onAbort={abort}
              />
            </div>
          </div>
        )}

        {(phase === 'generating' || phase === 'configure') && (
          <>
            <div className="w-5/12 overflow-hidden border-r border-gray-200">
              <BuilderChat
                onSubmitInitial={(p) => void handleSubmitInitial(p)}
                onSubmitRefine={(m) => void handleSubmitRefine(m)}
                onAbort={abort}
              />
            </div>
            <div className="w-7/12 overflow-hidden">
              <BuilderPreview />
            </div>
          </>
        )}

        {phase === 'testing' && (
          <>
            <div className="w-5/12 overflow-hidden border-r border-gray-200">
              <BuilderPreview />
            </div>
            <div className="w-7/12 overflow-hidden">
              <TestSandbox token={token} />
            </div>
          </>
        )}
      </div>

      {/* 底部操作栏 */}
      <BuilderActions
        onCancel={handleCancel}
        onStartTesting={() => void handleStartTesting()}
        onGoLive={() => void handleGoLive()}
        onBackToEdit={handleBackToEdit}
      />
    </div>
  );
}

// ── 内部子组件 ──

// input 阶段: 起步选择卡片（紧凑展示，下方留给 BuilderChat）
function InputPhaseHeader() {
  return (
    <div className="border-b border-gray-200 px-6 py-4">
      <div className="mx-auto max-w-2xl">
        <h2 className="text-center text-lg font-semibold text-gray-900">选择构建方式</h2>
        <div className="mt-3 grid grid-cols-3 gap-3">
          <StartOptionCard
            icon="📚"
            title="从 Skill 库"
            description="选择预置技能快速组装"
            disabled
          />
          <StartOptionCard icon="📋" title="从模板" description="基于行业模板快速定制" disabled />
          <StartOptionCard
            icon="💬"
            title="AI 引导"
            description="描述需求，AI 帮你生成蓝图"
            active
          />
        </div>
      </div>
    </div>
  );
}

function StartOptionCard({
  icon,
  title,
  description,
  active,
  disabled,
}: {
  icon: string;
  title: string;
  description: string;
  active?: boolean;
  disabled?: boolean;
}) {
  return (
    <div
      role="option"
      aria-selected={active}
      aria-disabled={disabled}
      title={disabled ? '即将上线' : undefined}
      className={`rounded-lg border-2 p-4 text-center transition-colors ${
        active
          ? 'border-blue-500 bg-blue-50'
          : disabled
            ? 'cursor-not-allowed border-gray-200 bg-gray-50 opacity-50'
            : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      <span className="text-2xl" aria-hidden="true">
        {icon}
      </span>
      <h3 className="mt-2 text-sm font-medium text-gray-900">{title}</h3>
      <p className="mt-1 text-xs text-gray-500">{description}</p>
      {active && (
        <span className="mt-2 inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
          推荐
        </span>
      )}
    </div>
  );
}
