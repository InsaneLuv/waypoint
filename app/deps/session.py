from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from app.repositories.redis_session_repository import RedisSessionRepository
from app.repositories.session_repository import SessionRepository
from app.services.session_service import SessionService


class SessionServiceProvider(Provider):
    """Провайдер сервисов сессий."""

    @provide(scope=Scope.REQUEST)
    def get_redis_session_repository(
            self,
            redis: Redis,
    ) -> RedisSessionRepository:
        """Создать Redis репозиторий."""
        return RedisSessionRepository(redis)

    @provide(scope=Scope.REQUEST)
    def get_session_repository(
            self,
            redis_repo: RedisSessionRepository,
    ) -> SessionRepository:
        """Получить репозиторий сессий."""
        return redis_repo

    @provide(scope=Scope.REQUEST)
    def get_session_service(
            self,
            repository: SessionRepository,
    ) -> SessionService:
        """Создать сервис управления сессиями."""
        return SessionService(repository)
