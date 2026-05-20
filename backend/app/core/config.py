from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
ENV_FILES = (
    BASE_DIR / ".env.example",
    BASE_DIR / ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "image2web"
    app_env: str = "development"
    debug: bool = False

    database_url: str = f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
    upload_image_dir: Path = Field(default=DATA_DIR / "uploads")
    generated_image_dir: Path = Field(default=DATA_DIR / "images")

    image2_base_url: str = ""
    image2_api_key: str = ""
    image2_model: str = "gpt-image-2"
    image2_timeout_seconds: float = 300.0

    admin_login_key: str = ""
    cors_origins: str = ""

    worker_poll_interval_seconds: int = 2
    worker_batch_size: int = 2
    task_timeout_seconds: int = 600
    task_max_retry_count: int = 1

    max_upload_images: int = 3
    max_upload_bytes: int = 10 * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_image_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_image_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.database_url.replace("sqlite:///", "")).parent.mkdir(
        parents=True, exist_ok=True
    )
    return settings
