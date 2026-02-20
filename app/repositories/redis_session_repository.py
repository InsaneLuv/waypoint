import json
from datetime import datetime
from uuid import UUID

from redis.asyncio import Redis

from app.models.discord import Session, SessionParticipant
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

    def _serialize_participant(self, participant: SessionParticipant) -> str:
        """Сериализовать участника в JSON."""
        return json.dumps({
            "user_id": participant.user_id,
            "username": participant.username,
            "joined_at": participant.joined_at.isoformat(),
        })

    def _deserialize_participant(self, data: str) -> SessionParticipant:
        """Десериализовать участника из JSON."""
        parsed = json.loads(data)
        return SessionParticipant(
            user_id=parsed["user_id"],
            username=parsed["username"],
            joined_at=datetime.fromisoformat(parsed["joined_at"]),
        )

    def _serialize_session(self, session: Session) -> dict:
        """Сериализовать сессию для хранения в Redis."""
        participants_data = [
            self._serialize_participant(p) for p in session.participants
        ]
        return {
            "id": str(session.id),
            "title": session.title,
            "description": session.description,
            "color": session.color.as_hex() if session.color else None,
            "created_at": session.created_at.isoformat(),
            "ends_at": session.ends_at.isoformat(),
            "state": session.state.value,
            "author_id": str(session.author_id) if session.author_id else None,
            "participants": json.dumps(participants_data),
        }

    def _deserialize_session(self, data: dict) -> Session:
        """Десериализовать данные из Redis в сессию."""
        participants = []
        participants_raw = data.get("participants")
        if participants_raw:
            participants_list = json.loads(participants_raw)
            participants = [
                self._deserialize_participant(p) for p in participants_list
            ]

        author_id_str = data.get("author_id")
        author_id = int(author_id_str) if author_id_str else None

        return Session(
            id=UUID(data["id"]),
            title=data["title"],
            description=data["description"],
            color=data.get("color"),
            created_at=datetime.fromisoformat(data["created_at"]),
            ends_at=datetime.fromisoformat(data["ends_at"]),
            state=int(data.get("state", 0)),
            author_id=author_id,
            participants=participants,
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

    async def add_participant(
        self,
        session_id: UUID,
        participant: SessionParticipant,
    ) -> Session:
        """Добавить участника в сессию."""
        session = await self.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session with id {session_id} not found")

        # Проверяем, нет ли уже такого участника
        for p in session.participants:
            if p.user_id == participant.user_id:
                return session  # Уже есть, ничего не делаем

        session.participants.append(participant)
        return await self.update(session)

    async def remove_participant(
        self,
        session_id: UUID,
        user_id: int,
    ) -> Session:
        """Удалить участника из сессии."""
        session = await self.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session with id {session_id} not found")

        session.participants = [
            p for p in session.participants if p.user_id != user_id
        ]
        return await self.update(session)
