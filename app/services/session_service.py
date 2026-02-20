from datetime import datetime, timedelta
from uuid import UUID, uuid4

from pydantic_extra_types.color import Color

from app.models.discord import DiscordColor, Session, SessionState
from app.repositories.session_repository import SessionRepository


class SessionService:
    """Сервис для управления сессиями.

    Содержит бизнес-логику приложения и использует репозиторий
    для доступа к данным. Не зависит от конкретной реализации хранилища.
    """

    DEFAULT_SESSION_DURATION_HOURS = 24

    def __init__(self, repository: SessionRepository):
        self.repository = repository

    async def create_session(
        self,
        title: str,
        description: str,
        color: Color | None = None,
        duration_hours: int | None = None,
    ) -> Session:
        """Создать новую сессию.

        Args:
            title: Заголовок сессии
            description: Описание сессии
            color: Цвет сессии (если не указан, выбирается случайный)
            duration_hours: Длительность сессии в часах

        Returns:
            Созданную сессию
        """
        if duration_hours is None:
            duration_hours = self.DEFAULT_SESSION_DURATION_HOURS

        now = datetime.utcnow()
        session = Session(
            id=uuid4(),
            title=title,
            description=description,
            color=color or DiscordColor.random(),
            created_at=now,
            ends_at=now + timedelta(hours=duration_hours),
            state=SessionState.undefined,
        )
        return await self.repository.create(session)

    async def get_session(self, session_id: UUID) -> Session | None:
        """Получить сессию по ID."""
        return await self.repository.get_by_id(session_id)

    async def get_all_sessions(self) -> list[Session]:
        """Получить все сессии."""
        return await self.repository.get_all()

    async def update_session(
        self,
        session_id: UUID,
        title: str | None = None,
        description: str | None = None,
        color: Color | None = None,
        state: SessionState | None = None,
    ) -> Session:
        """Обновить сессию.

        Args:
            session_id: ID сессии для обновления
            title: Новый заголовок (если указан)
            description: Новое описание (если указано)
            color: Новый цвет (если указан)
            state: Новое состояние (если указано)

        Returns:
            Обновлённую сессию

        Raises:
            ValueError: Если сессия не найдена
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session with id {session_id} not found")

        if title is not None:
            session.title = title
        if description is not None:
            session.description = description
        if color is not None:
            session.color = color
        if state is not None:
            session.state = state

        return await self.repository.update(session)

    async def delete_session(self, session_id: UUID) -> bool:
        """Удалить сессию.

        Returns:
            True если сессия удалена, False если не найдена
        """
        return await self.repository.delete(session_id)

    async def delete_all_sessions(self) -> int:
        """Удалить все сессии.

        Returns:
            Количество удалённых сессий
        """
        return await self.repository.delete_all()

    async def is_session_active(self, session_id: UUID) -> bool:
        """Проверить, активна ли сессия (не истекло ли время)."""
        session = await self.get_session(session_id)
        if not session:
            return False
        return datetime.utcnow() < session.ends_at
