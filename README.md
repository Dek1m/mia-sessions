# Sessions Module for Mia Framework

Управление сессиями LLM, участниками и историей сообщений.

## Features

- **Sessions** — создание, получение, архивация, список сессий
- **Participants** — агенты и пользователь в рамках сессии
- **Messages** — хранение и выборка истории сообщений
- **Multi-agent** — поддержка нескольких агентов в одной сессии
- **Интеграция с Task System** — операции через `@task`
- **Workspace-scoped** — сессии принадлежат workspace/project

## Hierarchy

```
Workspace (Project)
└── Session
    ├── Participants (user + agents)
    ├── Messages
    └── Runtime state
```

## Installation

```bash
git clone https://github.com/Dek1m/mia-sessions.git
cd mia-sessions
pip install -e .
```

## Configuration

### Environment Variables

```bash
SESSIONS_DEFAULT_MAX_MESSAGES=200
SESSIONS_DEFAULT_COMPACTION_THRESHOLD=0.8
SESSIONS_STORE_BACKEND=memory   # memory | postgres
```

### Direct Configuration

```python
from mia_sessions import SessionsModule, SessionsConfig

config = SessionsConfig(
    default_max_messages=200,
    store_backend="memory",
)

module = SessionsModule(config)
app.load_module(module)
```

## Usage

```python
# Создать сессию
session = app.services.resolve(SessionsProvider).create_session(
    workspace_id="proj-1",
    title="Debug auth flow",
    participant_ids=["user:sergey", "agent:coder"],
)

# Добавить сообщение
msg = app.services.resolve(SessionsProvider).add_message(
    session_id=session.id,
    role="user",
    content="Исправь баг в логине",
    sender_id="user:sergey",
)

# Получить историю
messages = app.services.resolve(SessionsProvider).get_messages(session.id)

# Добавить агента в сессию
app.services.resolve(SessionsProvider).add_participant(
    session_id=session.id,
    participant_id="agent:reviewer",
    role="agent",
)
```

## License

MIT
