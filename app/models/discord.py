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
        return random.choice(cls.COLORS)

class SessionState(enum.IntEnum):
    undefined = 0

class Session(BaseModel):
    id: UUID
    title: str
    description: str
    color: Color | None = Field(default=Color(value=DiscordColor.random()))
    created_at: datetime
    ends_at: datetime
    state: SessionState