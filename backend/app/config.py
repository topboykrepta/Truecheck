from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ENV_PATH = (Path(__file__).resolve().parents[1] / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_ENV_PATH), ".env"),
        env_ignore_empty=True,
        extra="ignore",
    )

    truecheck_env: str = "dev"
    truecheck_base_url: str = "http://localhost:8000"
    truecheck_cors_origins: str = "http://localhost:5173"

    truecheck_storage_dir: str = "./storage"
    truecheck_db_url: str = "sqlite:///./truecheck.db"

    truecheck_use_queue: int = 1
    truecheck_redis_url: str = "redis://localhost:6379/0"
    truecheck_queue_name: str = "truecheck"

    google_cse_api_key: str | None = None
    google_cse_engine_id: str | None = None

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    truecheck_rl_requests_per_minute: int = 60

    truecheck_search_cache_ttl_seconds: int = 60 * 60 * 12

    truecheck_max_image_matches_per_claim: int = 4
    truecheck_max_image_matches_total: int = 24

    def model_post_init(self, __context: Any) -> None:
        # Normalize placeholders/whitespace so config checks are reliable.
        def _norm(v: str | None) -> str | None:
            if v is None:
                return None
            s = v.strip()
            if not s:
                return None
            if s in {".", "YOUR_KEY_HERE", "YOUR_ENGINE_ID_HERE"}:
                return None
            return s

        self.google_cse_api_key = _norm(self.google_cse_api_key)
        self.google_cse_engine_id = _norm(self.google_cse_engine_id)
        self.gemini_api_key = _norm(self.gemini_api_key)


settings = Settings()
