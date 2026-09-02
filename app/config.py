from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.org import HR_EMAIL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://user:password@localhost:5432/incubyteesm"
    database_ssl_require: bool = True
    db_pool_size: int = 5
    db_max_overflow: int = 0

    hr_email: str = HR_EMAIL
    hr_password: str = "ChangeMeNow!"

    allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000,http://testserver,"
        "https://incubyteesm.fastapicloud.dev"
    )

    environment: str = "development"
    session_cookie_name: str = "iesm_session"
    csrf_cookie_name: str = "iesm_csrf"
    session_absolute_hours: int = 12
    session_idle_hours: int = 4

    def origin_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]

    @property
    def cookie_secure(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
