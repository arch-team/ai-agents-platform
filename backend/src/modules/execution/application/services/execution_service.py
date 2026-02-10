"""Execution 应用服务。"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

from src.modules.execution.application.dto.execution_dto import (
    ConversationDetailDTO,
    ConversationDTO,
    CreateConversationDTO,
    MessageDTO,
    PagedConversationDTO,
    SendMessageDTO,
)
from src.modules.execution.application.interfaces.llm_client import (
    ILLMClient,
    LLMMessage,
)
from src.modules.execution.domain.entities.conversation import Conversation
from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.events import (
    ConversationCompletedEvent,
    ConversationCreatedEvent,
    MessageReceivedEvent,
    MessageSentEvent,
)
from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
)
from src.modules.execution.domain.repositories.conversation_repository import (
    IConversationRepository,
)
from src.modules.execution.domain.repositories.message_repository import (
    IMessageRepository,
)
from src.modules.execution.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from src.modules.execution.domain.value_objects.message_role import MessageRole
from src.shared.domain.event_bus import event_bus
from src.shared.domain.exceptions import DomainError
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo, IAgentQuerier


@dataclass
class _SendContext:
    """send_message / send_message_stream 共享的前置准备结果。"""

    conversation: Conversation
    agent_info: ActiveAgentInfo
    created_user_msg: Message
    llm_messages: list[LLMMessage]


class ExecutionService:
    """Execution 业务服务，编排对话和消息的用例。"""

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        message_repo: IMessageRepository,
        llm_client: ILLMClient,
        agent_querier: IAgentQuerier,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._llm_client = llm_client
        self._agent_querier = agent_querier

    async def create_conversation(
        self,
        dto: CreateConversationDTO,
        user_id: int,
    ) -> ConversationDTO:
        """创建对话。校验 Agent ACTIVE 状态。发布 ConversationCreatedEvent。

        Raises:
            AgentNotAvailableError: Agent 不存在或非 ACTIVE
        """
        agent_info = await self._agent_querier.get_active_agent(dto.agent_id)
        if agent_info is None:
            raise AgentNotAvailableError(dto.agent_id)

        title = dto.title or f"与 {agent_info.name} 的对话"

        conversation = Conversation(
            title=title,
            agent_id=dto.agent_id,
            user_id=user_id,
        )
        created = await self._conversation_repo.create(conversation)
        assert created.id is not None

        await event_bus.publish_async(
            ConversationCreatedEvent(
                conversation_id=created.id,
                agent_id=dto.agent_id,
                user_id=user_id,
            ),
        )
        return self._to_conversation_dto(created)

    async def send_message(
        self,
        conversation_id: int,
        dto: SendMessageDTO,
        user_id: int,
    ) -> MessageDTO:
        """发送消息（同步）。

        Raises:
            ConversationNotFoundError, ConversationNotActiveError,
            DomainError(FORBIDDEN_CONVERSATION), AgentNotAvailableError
        """
        ctx = await self._prepare_for_send(conversation_id, dto.content, user_id)

        # 调用 LLM
        response = await self._llm_client.invoke(
            model_id=ctx.agent_info.model_id,
            messages=ctx.llm_messages,
            system_prompt=ctx.agent_info.system_prompt,
            temperature=ctx.agent_info.temperature,
            max_tokens=ctx.agent_info.max_tokens,
            top_p=ctx.agent_info.top_p,
            stop_sequences=ctx.agent_info.stop_sequences,
        )

        # 创建助手消息
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response.content,
            token_count=response.input_tokens + response.output_tokens,
        )
        created_assistant_msg = await self._message_repo.create(assistant_message)

        # 更新对话统计
        ctx.conversation.add_message_count(token_count=0)  # 用户消息
        ctx.conversation.add_message_count(
            token_count=response.input_tokens + response.output_tokens,
        )
        await self._conversation_repo.update(ctx.conversation)

        # 发布事件
        assert ctx.created_user_msg.id is not None
        assert created_assistant_msg.id is not None
        await event_bus.publish_async(
            MessageSentEvent(
                conversation_id=conversation_id,
                message_id=ctx.created_user_msg.id,
                user_id=user_id,
            ),
        )
        await event_bus.publish_async(
            MessageReceivedEvent(
                conversation_id=conversation_id,
                message_id=created_assistant_msg.id,
                token_count=response.input_tokens + response.output_tokens,
                model_id=ctx.agent_info.model_id,
            ),
        )

        return self._to_message_dto(created_assistant_msg)

    async def send_message_stream(
        self,
        conversation_id: int,
        dto: SendMessageDTO,
        user_id: int,
    ) -> AsyncIterator[str]:
        """发送消息（SSE 流式）。

        Raises:
            ConversationNotFoundError, ConversationNotActiveError,
            DomainError(FORBIDDEN_CONVERSATION), AgentNotAvailableError
        """
        ctx = await self._prepare_for_send(conversation_id, dto.content, user_id)

        # 创建空助手消息占位
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="",
        )
        created_assistant_msg = await self._message_repo.create(assistant_message)

        async def _generate() -> AsyncIterator[str]:
            collected_content = ""
            total_input_tokens = 0
            total_output_tokens = 0

            stream = await self._llm_client.invoke_stream(
                model_id=ctx.agent_info.model_id,
                messages=ctx.llm_messages,
                system_prompt=ctx.agent_info.system_prompt,
                temperature=ctx.agent_info.temperature,
                max_tokens=ctx.agent_info.max_tokens,
                top_p=ctx.agent_info.top_p,
                stop_sequences=ctx.agent_info.stop_sequences,
            )

            async for chunk in stream:
                if chunk.content:
                    collected_content += chunk.content
                    yield f"data: {json.dumps({'content': chunk.content, 'done': False})}\n\n"

                if chunk.done:
                    total_input_tokens = chunk.input_tokens
                    total_output_tokens = chunk.output_tokens

            total_tokens = total_input_tokens + total_output_tokens
            created_assistant_msg.content = collected_content
            created_assistant_msg.token_count = total_tokens
            await self._message_repo.update(created_assistant_msg)

            # 更新对话统计
            ctx.conversation.add_message_count(token_count=0)  # 用户消息
            ctx.conversation.add_message_count(token_count=total_tokens)
            await self._conversation_repo.update(ctx.conversation)

            # 发布事件
            assert ctx.created_user_msg.id is not None
            assert created_assistant_msg.id is not None
            await event_bus.publish_async(
                MessageSentEvent(
                    conversation_id=conversation_id,
                    message_id=ctx.created_user_msg.id,
                    user_id=user_id,
                ),
            )
            await event_bus.publish_async(
                MessageReceivedEvent(
                    conversation_id=conversation_id,
                    message_id=created_assistant_msg.id,
                    token_count=total_tokens,
                    model_id=ctx.agent_info.model_id,
                ),
            )

            done_data = json.dumps(
                {
                    "content": "",
                    "done": True,
                    "message_id": created_assistant_msg.id,
                    "token_count": total_tokens,
                },
            )
            yield f"data: {done_data}\n\n"

        return _generate()

    async def get_conversation(
        self,
        conversation_id: int,
        user_id: int,
    ) -> ConversationDetailDTO:
        """获取对话详情（含消息历史）。校验所有权。

        Raises:
            ConversationNotFoundError, DomainError(FORBIDDEN_CONVERSATION)
        """
        conversation = await self._get_conversation_or_raise(conversation_id)
        self._check_ownership(conversation, user_id)

        messages = await self._message_repo.list_by_conversation(conversation_id)
        return ConversationDetailDTO(
            conversation=self._to_conversation_dto(conversation),
            messages=[self._to_message_dto(m) for m in messages],
        )

    async def list_conversations(
        self,
        user_id: int,
        *,
        agent_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedConversationDTO:
        """获取对话列表。"""
        offset = (page - 1) * page_size

        conversations = await self._conversation_repo.list_by_user(
            user_id,
            agent_id=agent_id,
            offset=offset,
            limit=page_size,
        )
        total = await self._conversation_repo.count_by_user(
            user_id,
            agent_id=agent_id,
        )

        return PagedConversationDTO(
            items=[self._to_conversation_dto(c) for c in conversations],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def complete_conversation(
        self,
        conversation_id: int,
        user_id: int,
    ) -> ConversationDTO:
        """结束对话。校验所有权。发布 ConversationCompletedEvent。

        Raises:
            ConversationNotFoundError, DomainError(FORBIDDEN_CONVERSATION),
            InvalidStateTransitionError
        """
        conversation = await self._get_conversation_or_raise(conversation_id)
        self._check_ownership(conversation, user_id)

        conversation.complete()
        updated = await self._conversation_repo.update(conversation)

        await event_bus.publish_async(
            ConversationCompletedEvent(
                conversation_id=conversation_id,
                user_id=user_id,
            ),
        )
        return self._to_conversation_dto(updated)

    # ── 内部辅助方法 ──

    async def _prepare_for_send(
        self,
        conversation_id: int,
        content: str,
        user_id: int,
    ) -> _SendContext:
        """send_message / send_message_stream 共有的前置逻辑。

        校验对话存在、所有权、活跃状态；校验 Agent 可用；
        创建用户消息；加载历史并构建 LLM 上下文。
        """
        conversation = await self._get_conversation_or_raise(conversation_id)
        self._check_ownership(conversation, user_id)
        self._check_active(conversation)

        agent_info = await self._agent_querier.get_active_agent(conversation.agent_id)
        if agent_info is None:
            raise AgentNotAvailableError(conversation.agent_id)

        # 创建用户消息
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )
        created_user_msg = await self._message_repo.create(user_message)

        # 加载消息历史 → 构建 LLM 上下文
        history = await self._message_repo.list_by_conversation(conversation_id)
        llm_messages = [LLMMessage(role=m.role.value, content=m.content) for m in history]

        return _SendContext(
            conversation=conversation,
            agent_info=agent_info,
            created_user_msg=created_user_msg,
            llm_messages=llm_messages,
        )

    async def _get_conversation_or_raise(
        self,
        conversation_id: int,
    ) -> Conversation:
        conversation = await self._conversation_repo.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation

    @staticmethod
    def _check_ownership(conversation: Conversation, user_id: int) -> None:
        """校验对话所有权。"""
        if conversation.user_id != user_id:
            raise DomainError(
                message="无权操作此对话",
                code="FORBIDDEN_CONVERSATION",
            )

    @staticmethod
    def _check_active(conversation: Conversation) -> None:
        """校验对话处于活跃状态。"""
        if conversation.status != ConversationStatus.ACTIVE:
            assert conversation.id is not None
            raise ConversationNotActiveError(conversation.id)

    @staticmethod
    def _to_conversation_dto(conv: Conversation) -> ConversationDTO:
        assert conv.id is not None
        assert conv.created_at is not None
        assert conv.updated_at is not None
        return ConversationDTO(
            id=conv.id,
            title=conv.title,
            agent_id=conv.agent_id,
            user_id=conv.user_id,
            status=conv.status.value,
            message_count=conv.message_count,
            total_tokens=conv.total_tokens,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    @staticmethod
    def _to_message_dto(msg: Message) -> MessageDTO:
        assert msg.id is not None
        assert msg.created_at is not None
        return MessageDTO(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role.value,
            content=msg.content,
            token_count=msg.token_count,
            created_at=msg.created_at,
        )
