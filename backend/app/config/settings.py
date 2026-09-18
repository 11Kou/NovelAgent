from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    openai_fallback_model: str = "gpt-4o-mini"

    ollama_host: str = "http://127.0.0.1:11434"
    ollama_embedding_model: str = "bge-m3"

    database_url: str = "sqlite:///data/story.db"
    chroma_path: str = "data/chroma"
    model_timeout_seconds: int = Field(default=120, ge=5)
    model_max_retries: int = Field(default=1, ge=0, le=5)
    recent_chapter_window: int = Field(default=3, ge=1)
    rolling_summary_interval: int = Field(default=5, ge=1)
    prompt_token_budget: int = Field(default=7000, ge=1000)

    backend_cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    def ensure_data_dirs(self) -> None:
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)

    def normalize_paths(self) -> None:
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.removeprefix("sqlite:///"))
            if not db_path.is_absolute():
                db_path = ROOT_ENV.parent / db_path
            self.database_url = f"sqlite:///{db_path.as_posix()}"

        chroma_path = Path(self.chroma_path)
        if not chroma_path.is_absolute():
            chroma_path = ROOT_ENV.parent / chroma_path
        self.chroma_path = str(chroma_path)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.normalize_paths()
    settings.ensure_data_dirs()
    return settings
