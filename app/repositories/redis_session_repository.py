import json
from datetime import datetime
from uuid import UUID

from redis.asyncio import Redis

from app.models.discord import Session
from app.repositories.session_repository import SessionRepository


class RedisSessionRepository(SessionRepository):
    """Redis-реализация репозитория сессий.

    Использует Redis Hash для хранения данных сессии.
    Ключи имеют префикс 'session:' для изоляции данных.
    """

    KEY_PREFIX = "session:"
    ALL_SESSIONS_KEY = "sessions:all"

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def _get_key(self, session_id: UUID) -> str:
        """Сформировать ключ для сессии в Redis."""
        return f"{self.KEY_PREFIX}{session_id}"

    def _serialize_session(self, session: Session) -> dict:
        """Сериализовать сессию для хранения в Redis."""
        return {
            "id": str(session.id),
            "title": session.title,
            "description": session.description,
            "color": session.color.as_hex() if session.color else None,
            "created_at": session.created_at.isoformat(),
            "ends_at": session.ends_at.isoformat(),
            "state": session.state.value,
        }

    def _deserialize_session(self, data: dict) -> Session:
        """Десериализовать данные из Redis в сессию."""
        return Session(
            id=UUID(data["id"]),
            title=data["title"],
            description=data["description"],
            color=data.get("color"),
            created_at=datetime.fromisoformat(data["created_at"]),
            ends_at=datetime.fromisoformat(data["ends_at"]),
            state=int(data.get("state", 0)),
        )

    async def create(self, session: Session) -> Session:
        key = self._get_key(session.id)
        data = self._serialize_session(session)
        await self.redis.hset(key, mapping=data)
        await self.redis.sadd(self.ALL_SESSIONS_KEY, str(session.id))
        return session

    async def get_by_id(self, session_id: UUID) -> Session | None:
        key = self._get_key(session_id)
        data = await self.redis.hgetall(key)
        if not data:
            return None
        # Декодируем байты в строки
        decoded_data = {k.decode(): v.decode() for k, v in data.items()}
        return self._deserialize_session(decoded_data)

    async def get_all(self) -> list[Session]:
        session_ids = await self.redis.smembers(self.ALL_SESSIONS_KEY)
        sessions = []
        for session_id_bytes in session_ids:
            session_id = UUID(session_id_bytes.decode())
            session = await self.get_by_id(session_id)
            if session:
                sessions.append(session)
        return sessions

    async def update(self, session: Session) -> Session:
        key = self._get_key(session.id)
        exists = await self.redis.exists(key)
        if not exists:
            raise ValueError(f"Session with id {session.id} does not exist")
        data = self._serialize_session(session)
        await self.redis.hset(key, mapping=data)
        return session

    async def delete(self, session_id: UUID) -> bool:
        key = self._get_key(session_id)
        deleted = await self.redis.delete(key)
        if deleted:
            await self.redis.srem(self.ALL_SESSIONS_KEY, str(session_id))
        return bool(deleted)

    async def delete_all(self) -> int:
        session_ids = await self.redis.smembers(self.ALL_SESSIONS_KEY)
        if not session_ids:
            return 0
        keys = [self._get_key(UUID(sid.decode())) for sid in session_ids]
        deleted = await self.redis.delete(*keys)
        await self.redis.delete(self.ALL_SESSIONS_KEY)
        return deleted
