from typing import Literal

from dishka import provide, Provider, Scope

from app.core.config import AppSettings, get_app_settings


class ConfigProvider(Provider):
    """Провайдер конфигураций приложения"""

    def __init__(self, scope: Literal["prod", "test"] = "prod"):
        super().__init__()
        self.settings_scope = scope

    @provide(scope=Scope.APP)
    def get_settings(self) -> AppSettings:
        return get_app_settings(self.settings_scope)
