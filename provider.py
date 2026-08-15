"""Sessions Provider — управление сессиями, участниками и сообщениями."""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from argenta_logging import get_logger

try:
    from core.task_decorator import task
except ImportError:
    def task(**kwargs):  # type: ignore
        def deco(fn):
            return fn
        return deco

from .config import SessionsConfig
from .models import (
    Message,
    MessageRole,
    Participant,
    ParticipantRole,
    Session,
    SessionStatus,
)

log = get_logger(__name__)

__all__ = ["SessionsProvider"]


class SessionsProvider:
    """Провайдер сессий.

    In-memory реализация (store_backend=memory).
    Позже можно добавить Postgres backend.
    """

    def __init__(self, config: SessionsConfig) -> None:
        self._config = config
        self._sessions: dict[UUID, Session] = {}
        self._messages: dict[UUID, list[Message]] = {}  # session_id -> messages
        self._lock = threading.RLock()

    # ── Sessions ──────────────────────────────────────────────

    @task(type="io", timeout=5.0)
    def create_session(
        self,
        workspace_id: str,
        title: str | None = None,
        participant_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Создать новую сессию."""
        title = title or self._config.default_title
        participants: list[Participant] = []

        if participant_ids:
            for pid in participant_ids:
                role = ParticipantRole.AGENT if pid.startswith("agent:") else ParticipantRole.USER
                participants.append(
                    Participant(id=pid, role=role, display_name=pid)
                )

        session = Session.create(
            workspace_id=workspace_id,
            title=title,
            participants=participants,
            metadata=metadata or {},
        )

        with self._lock:
            self._sessions[session.id] = session
            self._messages[session.id] = []

        log.info("session_created", session_id=str(session.id), workspace_id=workspace_id)
        return session

    @task(type="io", timeout=5.0)
    def get_session(self, session_id: UUID | str) -> Session | None:
        sid = UUID(str(session_id))
        with self._lock:
            return self._sessions.get(sid)

    @task(type="io", timeout=5.0)
    def list_sessions(
        self,
        workspace_id: str | None = None,
        status: SessionStatus | str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        with self._lock:
            items = list(self._sessions.values())

        if workspace_id:
            items = [s for s in items if s.workspace_id == workspace_id]
        if status:
            st = SessionStatus(status) if isinstance(status, str) else status
            items = [s for s in items if s.status == st]

        items.sort(key=lambda s: s.updated_at, reverse=True)
        return items[offset : offset + limit]

    @task(type="io", timeout=5.0)
    def archive_session(self, session_id: UUID | str) -> Session | None:
        sid = UUID(str(session_id))
        with self._lock:
            session = self._sessions.get(sid)
            if not session:
                return None
            session.status = SessionStatus.ARCHIVED
            session.updated_at = datetime.now(timezone.utc)
            return session

    # ── Participants ──────────────────────────────────────────

    @task(type="io", timeout=5.0)
    def add_participant(
        self,
        session_id: UUID | str,
        participant_id: str,
        role: ParticipantRole | str = ParticipantRole.AGENT,
        display_name: str | None = None,
        agent_definition_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Participant | None:
        if not self._config.allow_multi_agent and role == ParticipantRole.AGENT:
            # Можно добавить проверку на количество агентов
            pass

        sid = UUID(str(session_id))
        role = ParticipantRole(role) if isinstance(role, str) else role

        participant = Participant(
            id=participant_id,
            role=role,
            display_name=display_name or participant_id,
            agent_definition_id=agent_definition_id,
            metadata=metadata or {},
        )

        with self._lock:
            session = self._sessions.get(sid)
            if not session:
                return None
            # Не дублируем
            if any(p.id == participant_id for p in session.participants):
                return next(p for p in session.participants if p.id == participant_id)
            session.participants.append(participant)
            session.updated_at = datetime.now(timezone.utc)
            return participant

    @task(type="io", timeout=5.0)
    def remove_participant(self, session_id: UUID | str, participant_id: str) -> bool:
        sid = UUID(str(session_id))
        with self._lock:
            session = self._sessions.get(sid)
            if not session:
                return False
            before = len(session.participants)
            session.participants = [p for p in session.participants if p.id != participant_id]
            session.updated_at = datetime.now(timezone.utc)
            return len(session.participants) < before

    # ── Messages ──────────────────────────────────────────────

    @task(type="io", timeout=5.0)
    def add_message(
        self,
        session_id: UUID | str,
        role: MessageRole | str,
        content: str,
        sender_id: str | None = None,
        parent_id: UUID | str | None = None,
        tool_calls: list[dict] | None = None,
        metadata: dict[str, Any] | None = None,
        tokens: int | None = None,
    ) -> Message | None:
        sid = UUID(str(session_id))
        pid = UUID(str(parent_id)) if parent_id else None

        msg = Message.create(
            session_id=sid,
            role=role,
            content=content,
            sender_id=sender_id,
            parent_id=pid,
            tool_calls=tool_calls,
            metadata=metadata or {},
            tokens=tokens,
        )

        with self._lock:
            session = self._sessions.get(sid)
            if not session:
                return None
            self._messages.setdefault(sid, []).append(msg)
            session.message_count = len(self._messages[sid])
            session.updated_at = datetime.now(timezone.utc)
            return msg

    @task(type="io", timeout=5.0)
    def get_messages(
        self,
        session_id: UUID | str,
        limit: int | None = None,
        offset: int = 0,
        after_id: UUID | str | None = None,
    ) -> list[Message]:
        sid = UUID(str(session_id))
        with self._lock:
            messages = list(self._messages.get(sid, []))

        if after_id:
            aid = UUID(str(after_id))
            idx = next((i for i, m in enumerate(messages) if m.id == aid), None)
            if idx is not None:
                messages = messages[idx + 1 :]

        if offset:
            messages = messages[offset:]
        if limit is not None:
            messages = messages[:limit]
        return messages

    @task(type="io", timeout=5.0)
    def get_message_count(self, session_id: UUID | str) -> int:
        sid = UUID(str(session_id))
        with self._lock:
            return len(self._messages.get(sid, []))
