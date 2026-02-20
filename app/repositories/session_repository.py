from abc import ABC, abstractmethod
from uuid import UUID

from app.models.discord import Session, SessionParticipant


class SessionRepository(ABC):
    """Абстрактный репозиторий для управления сессиями.

    Интерфейс определяет контракт для работы с сессиями,
    что позволяет легко менять реализацию хранилища (Redis, PostgreSQL, etc.).
    """

    @abstractmethod
    async def create(self, session: Session) -> Session:
        """Создать новую сессию."""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Session | None:
        """Получить сессию по ID."""
        pass

    @abstractmethod
    async def get_all(self) -> list[Session]:
        """Получить все сессии."""
        pass

    @abstractmethod
    async def update(self, session: Session) -> Session:
        """Обновить существующую сессию."""
        pass

    @abstractmethod
    async def delete(self, session_id: UUID) -> bool:
        """Удалить сессию по ID."""
        pass

    @abstractmethod
    async def delete_all(self) -> int:
        """Удалить все сессии. Возвращает количество удалённых."""
        pass

    @abstractmethod
    async def add_participant(
        self,
        session_id: UUID,
        participant: SessionParticipant,
    ) -> Session:
        """Добавить участника в сессию."""
        pass

    @abstractmethod
    async def remove_participant(
        self,
        session_id: UUID,
        user_id: int,
    ) -> Session:
        """Удалить участника из сессии."""
        pass
