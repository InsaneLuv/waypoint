from pydantic import Field, Secret
from pydantic_settings import SettingsConfigDict

from app.core.settings.app import AppBase


class ProdAppSettings(AppBase):
    model_config = SettingsConfigDict(env_file=".env")

    BOT_TOKEN: Secret[str] = Field()

    # Redis settings
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)