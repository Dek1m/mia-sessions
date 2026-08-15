"""Sessions Module Configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

__all__ = ["SessionsConfig"]


@dataclass
class SessionsConfig:
    """Конфигурация модуля сессий.

    Приоритет:
    1. Прямые аргументы
    2. Переменные окружения
    """

    # Лимиты
    default_max_messages: int = 200
    default_compaction_threshold: float = 0.8  # доля от max_messages

    # Хранилище
    store_backend: str = "memory"  # memory | postgres

    # Поведение
    auto_add_user: bool = True
    allow_multi_agent: bool = True

    # Мета
    default_title: str = "New session"

    @classmethod
    def from_env(cls) -> SessionsConfig:
        return cls(
            default_max_messages=int(os.getenv("SESSIONS_DEFAULT_MAX_MESSAGES", "200")),
            default_compaction_threshold=float(
                os.getenv("SESSIONS_DEFAULT_COMPACTION_THRESHOLD", "0.8")
            ),
            store_backend=os.getenv("SESSIONS_STORE_BACKEND", "memory"),
            auto_add_user=os.getenv("SESSIONS_AUTO_ADD_USER", "true").lower() == "true",
            allow_multi_agent=os.getenv("SESSIONS_ALLOW_MULTI_AGENT", "true").lower() == "true",
            default_title=os.getenv("SESSIONS_DEFAULT_TITLE", "New session"),
        )
