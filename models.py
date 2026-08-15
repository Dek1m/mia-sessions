"""Модели данных модуля Sessions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SessionStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPACTING = "compacting"


class ParticipantRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Participant:
    """Участник сессии."""

    id: str                          # user:xxx | agent:xxx
    role: ParticipantRole
    display_name: str | None = None
    agent_definition_id: str | None = None  # ссылка на шаблон агента
    metadata: dict[str, Any] = field(default_factory=dict)
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Message:
    """Сообщение в сессии."""

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    sender_id: str | None = None     # participant id
    parent_id: UUID | None = None    # для tool calls / replies
    tool_calls: list[dict] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tokens: int | None = None

    @classmethod
    def create(
        cls,
        session_id: UUID,
        role: MessageRole | str,
        content: str,
        sender_id: str | None = None,
        **kwargs: Any,
    ) -> Message:
        if isinstance(role, str):
            role = MessageRole(role)
        return cls(
            id=uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            sender_id=sender_id,
            **kwargs,
        )


@dataclass
class Session:
    """Сессия общения."""

    id: UUID
    workspace_id: str
    title: str
    status: SessionStatus = SessionStatus.ACTIVE
    participants: list[Participant] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0

    @classmethod
    def create(
        cls,
        workspace_id: str,
        title: str = "New session",
        participants: list[Participant] | None = None,
        **kwargs: Any,
    ) -> Session:
        return cls(
            id=uuid4(),
            workspace_id=workspace_id,
            title=title,
            participants=participants or [],
            **kwargs,
        )
