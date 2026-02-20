from redis.asyncio import Redis

from app.core.settings.production import ProdAppSettings
from dishka import Provider, Scope, provide


class RedisProvider(Provider):
    """Провайдер Redis клиента."""

    @provide(scope=Scope.APP)
    def get_redis(self, settings: ProdAppSettings) -> Redis:
        """Создать Redis клиент."""
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=False,
        )
