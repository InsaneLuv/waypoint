from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from app.core.config import AppSettings


class RedisProvider(Provider):
    """Провайдер Redis клиента."""

    @provide(scope=Scope.APP)
    def get_redis(self, settings: AppSettings) -> Redis:
        """Создать Redis клиент."""
        settings = settings.app
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=False,
        )
