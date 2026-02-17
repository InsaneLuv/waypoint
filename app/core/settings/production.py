from pydantic import Field, Secret
from pydantic_settings import SettingsConfigDict

from app.core.settings.app import AppBase


class ProdAppSettings(AppBase):
    model_config = SettingsConfigDict(env_file=".env")

    BOT_TOKEN: Secret[str] = Field()