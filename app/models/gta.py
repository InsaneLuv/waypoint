import uuid
from uuid import UUID

from pydantic import BaseModel, Field


class Stack(BaseModel):
    uuid: UUID
    name: str
    points: list[Point] = Field(default_factory=list)


class Point(BaseModel):
    uuid: UUID
    x: float
    y: float
    z: float | None = Field(default=None)
    level: int | None = Field(default=0)
    number: str | None = Field(default="?")

test_points = [
    Point(x=1, y=2, level=1, number="1", uuid=uuid.uuid4()),
    Point(x=1, y=2, level=1, number="2", uuid=uuid.uuid4()),
    Point(x=1, y=2, level=1, number="3", uuid=uuid.uuid4()),
    Point(x=1, y=2, level=1, number="4", uuid=uuid.uuid4()),
]

test_stack = Stack(uuid=uuid.uuid4(), name="test", points=test_points)