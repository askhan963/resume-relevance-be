import os
from enum import Enum

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    APP_NAME: str = "Resume Relevance & ATS Optimizer API"
    APP_DESCRIPTION: str | None = (
        "AI-powered backend for Resume Relevance Scoring, ATS Optimization, and Resume Rewriting."
    )
    APP_VERSION: str | None = "1.0.0"
    LICENSE_NAME: str | None = "MIT"
    CONTACT_NAME: str | None = None
    CONTACT_EMAIL: str | None = None
    LOG_REQUEST_BODY: bool = True
    LOG_RESPONSE_BODY: bool = True
    LOG_MAX_BODY_SIZE: int = 10240  # 10KB limit


class CryptSettings(BaseSettings):
    SECRET_KEY: SecretStr = SecretStr("change-this-secret-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class FileLoggerSettings(BaseSettings):
    FILE_LOG_MAX_BYTES: int = 10 * 1024 * 1024
    FILE_LOG_BACKUP_COUNT: int = 5
    FILE_LOG_FORMAT_JSON: bool = True
    FILE_LOG_LEVEL: str = "INFO"

    FILE_LOG_INCLUDE_REQUEST_ID: bool = True
    FILE_LOG_INCLUDE_PATH: bool = True
    FILE_LOG_INCLUDE_METHOD: bool = True
    FILE_LOG_INCLUDE_CLIENT_HOST: bool = True
    FILE_LOG_INCLUDE_STATUS_CODE: bool = True


class ConsoleLoggerSettings(BaseSettings):
    CONSOLE_LOG_LEVEL: str = "INFO"
    CONSOLE_LOG_FORMAT_JSON: bool = False

    CONSOLE_LOG_INCLUDE_REQUEST_ID: bool = False
    CONSOLE_LOG_INCLUDE_PATH: bool = False
    CONSOLE_LOG_INCLUDE_METHOD: bool = False
    CONSOLE_LOG_INCLUDE_CLIENT_HOST: bool = False
    CONSOLE_LOG_INCLUDE_STATUS_CODE: bool = False


class DatabaseSettings(BaseSettings):
    pass


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "resume_optimizer"
    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
    POSTGRES_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> str:
        # Allow full URL override (useful for Supabase connection strings)
        if self.POSTGRES_URL:
            return self.POSTGRES_URL
        credentials = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        location = f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"{credentials}@{location}"


class FirstUserSettings(BaseSettings):
    ADMIN_NAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"


class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379
    REDIS_CACHE_ENABLED: bool = False  # Optional — disable if no Redis available

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_CACHE_URL(self) -> str:
        return f"redis://{self.REDIS_CACHE_HOST}:{self.REDIS_CACHE_PORT}"


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = 60


class SupabaseSettings(BaseSettings):
    """Supabase project settings for Storage integration."""

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""  # Service role key (not anon key) for server-side ops
    SUPABASE_STORAGE_BUCKET: str = "resumes"


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    # Groq (Llama 3) — primary provider
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"

    # Google Gemini — fallback / alternative provider
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Default provider: "groq" or "gemini"
    DEFAULT_LLM_PROVIDER: str = "groq"

    # LLM generation settings
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 4096


class FileSettings(BaseSettings):
    """File upload configuration."""

    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: list[str] = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx"]


class EnvironmentOption(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL


class CORSSettings(BaseSettings):
    CORS_ORIGINS: list[str] = ["*"]
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]


class Settings(
    AppSettings,
    PostgresSettings,
    CryptSettings,
    FirstUserSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    SupabaseSettings,
    LLMSettings,
    FileSettings,
    EnvironmentSettings,
    CORSSettings,
    FileLoggerSettings,
    ConsoleLoggerSettings,
):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
