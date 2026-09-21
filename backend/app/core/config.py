from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PhoenixML"
    API_V1_STR: str = "/api"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./phoenixml.db"
    JWT_SECRET_KEY: str = "dev-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)


settings = Settings()
