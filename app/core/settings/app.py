from pydantic_settings import BaseSettings


class AppBase(BaseSettings):
    version: str = "0.0.0"
