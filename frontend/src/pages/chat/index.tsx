// 聊天页面 — 左侧对话列表 + 右侧聊天界面
import { useNavigate, useParams } from 'react-router-dom';

import { useAuthToken } from '@/features/auth';
import { ChatInterface, ConversationList } from '@/features/execution';

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const token = useAuthToken();

  const currentId = conversationId ? Number(conversationId) : null;

  const handleSelectConversation = (id: number) => {
    navigate(`/chat/${id}`);
  };

  // Fix [REACT-2]: 移除多余的 async
  const handleNewConversation = () => {
    // 新对话需要从 Agent 详情页发起（需 agent_id），此处仅支持导航到 agents 页面
    navigate('/agents');
  };

  return (
    <div className="flex h-full">
      {/* 左侧: 对话列表 */}
      <ConversationList
        selectedId={currentId}
        onSelect={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />

      {/* 右侧: 对话界面 */}
      <div className="flex-1">
        {currentId ? (
          <ChatInterface conversationId={currentId} token={token} />
        ) : (
          <div className="flex h-full items-center justify-center text-gray-400">
            <p>请选择一个对话</p>
          </div>
        )}
      </div>
    </div>
  );
}
