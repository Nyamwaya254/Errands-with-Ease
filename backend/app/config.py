import os
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# _base_config = SettingsConfigDict(
#     env_file=".env", env_ignore_empty=True, extra="ignore"
# )

_base_config = SettingsConfigDict(
    env_file=".env.test" if os.getenv("TESTING") else ".env",
    env_ignore_empty=True,
    extra="ignore",
)


class AppSettings(BaseSettings):
    APP_NAME: str = "ERRANDS WITH EASE"
    APP_DOMAIN: str = "localhost:8000"

    model_config = _base_config


class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_PASSWORD: str

    model_config = _base_config

    @property
    def POSTGRES_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{quote_plus(self.POSTGRES_PASSWORD)}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


app_settings = AppSettings()
db_settings = DatabaseSettings()  # type:ignore
