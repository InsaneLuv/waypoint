import enum
import random
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic_extra_types.color import Color


class DiscordColor:
    COLORS: list[str] = [
        "#2C3E50",  # Midnight Blue
        "#E74C3C",  # Alizarin Crimson
        "#3498DB",  # Peter River
        "#9B59B6",  # Amethyst
        "#1ABC9C",  # Turquoise
        "#F39C12",  # Orange
        "#34495E",  # Wet Asphalt
        "#16A085",  # Green Sea
        "#C0392B",  # Pomegranate
        "#8E44AD",  # Wisteria
    ]

    @classmethod
    def random(cls) -> Color:
        return Color(random.choice(cls.COLORS))

    @classmethod
    def random_hex(cls) -> str:
        c = random.choice(cls.COLORS)
        return hex(c)


class SessionState(enum.IntEnum):
    undefined = 0


class SessionParticipant(BaseModel):
    """Участник сессии."""
    user_id: int
    username: str
    joined_at: datetime


class SwitchPolicy(BaseModel):
    guest_can_switch_point: bool = Field(default=False, description="Может ли участник переключать точки")
    guest_can_switch_stack: bool = Field(default=False, description="Может ли участник переключать стеки с точками")


class SessionPolicy(BaseModel):
    free_session: bool = Field(default=True, description="Подключение без приглашения")
    guest_can_invite: bool = Field(default=False, description="Может ли участник приглашать гостей")


class ExternalSettings(BaseModel):
    enabled: bool = Field(default=True, description="Переключение внешними инструментами")

    switch_point_next_webhook: str | None = Field(default=None)
    switch_point_prev_webhook: str | None = Field(default=None)

    switch_stack_next_webhook: str | None = Field(default=None)
    switch_stack_prev_webhook: str | None = Field(default=None)


class SessionSettings(BaseModel):
    switch_policy: SwitchPolicy
    session_policy: SessionPolicy
    external_policy: ExternalSettings


class Session(BaseModel):
    id: UUID
    title: str
    description: str
    color: Color | None = Field(default=Color(value=DiscordColor.random()))
    created_at: datetime
    ends_at: datetime
    state: SessionState
    author_id: int | None = None
    participants: list[SessionParticipant] = Field(default_factory=list)
