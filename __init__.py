"""Sessions Module — модуль сессий для Mia Framework.

Управляет сессиями LLM, участниками и историей сообщений.

Использование:
    app.load_module("sessions")

    provider = app.services.resolve(SessionsProvider)
    session = provider.create_session(workspace_id="proj-1", title="Debug")
"""
from __future__ import annotations

from typing import Any

from modules_system.module_base import ModuleBase

from .config import SessionsConfig
from .provider import SessionsProvider
from .models import (
    Message,
    MessageRole,
    Participant,
    ParticipantRole,
    Session,
    SessionStatus,
)

__all__ = [
    "SessionsModule",
    "SessionsProvider",
    "SessionsConfig",
    "Session",
    "SessionStatus",
    "Participant",
    "ParticipantRole",
    "Message",
    "MessageRole",
]

from argenta_logging import get_logger

log = get_logger(__name__)

MODULE_VERSION = "0.1.0"


class SessionsModule(ModuleBase):
    """Sessions-модуль для Mia Framework.

    Предоставляет:
    - Создание и управление сессиями
    - Участников (user + agents)
    - Историю сообщений
    - Интеграцию с Task System
    """

    @property
    def name(self) -> str:
        return "sessions"

    @property
    def version(self) -> str:
        return MODULE_VERSION

    def __init__(self, config: SessionsConfig | None = None) -> None:
        self._config = config or SessionsConfig.from_env()
        self._provider: SessionsProvider | None = None

    def on_load(self, state: Any) -> None:
        """Инициализация модуля и регистрация провайдера в DI."""
        self._provider = SessionsProvider(self._config)

        # Регистрация в ServiceRegistry, если доступен
        try:
            if hasattr(state, "services") and hasattr(state.services, "register"):
                state.services.register(SessionsProvider, self._provider)
                log.info("SessionsProvider registered in DI")
        except Exception as exc:
            log.warning("failed_to_register_sessions_provider", error=str(exc))

        log.info(
            "sessions_module_loaded",
            version=self.version,
            store_backend=self._config.store_backend,
        )

    def on_unload(self) -> None:
        self._provider = None
        log.info("sessions_module_unloaded")
