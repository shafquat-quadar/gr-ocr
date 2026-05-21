from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "gr-agent-poc"
    APP_ENV: str = "local"

    SAP_MODE: Literal["mock", "real"] = "mock"
    SAP_AUTH_TYPE: Literal["basic", "bearer"] = "basic"

    DATABASE_URL: str = "sqlite:///./db/gr_agent.sqlite"
    UPLOAD_DIR: str = "./uploads"

    OCR_ENGINE: str = "tesseract"
    TESSERACT_CMD: str = "/usr/bin/tesseract"

    SAP_BASE_URL: str = ""
    SAP_CLIENT: str = ""
    SAP_USER: str = ""
    SAP_PASSWORD: str = ""
    SAP_BEARER_TOKEN: str = ""
    SAP_VERIFY_SSL: bool = False
    SAP_TIMEOUT_SECONDS: int = 60

    MAX_UPLOAD_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png"
    REQUIRE_HUMAN_CONFIRMATION: bool = True

    @field_validator("SAP_VERIFY_SSL", mode="before")
    @classmethod
    def parse_ssl(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)

    @model_validator(mode="after")
    def validate_real_sap_config(self) -> "Settings":
        if self.SAP_MODE != "real":
            return self
        if not self.SAP_BASE_URL:
            raise ValueError("SAP_BASE_URL is required when SAP_MODE=real")
        if self.SAP_AUTH_TYPE == "basic":
            if not self.SAP_USER or not self.SAP_PASSWORD:
                raise ValueError(
                    "SAP_USER and SAP_PASSWORD are required when SAP_MODE=real and SAP_AUTH_TYPE=basic"
                )
        elif self.SAP_AUTH_TYPE == "bearer":
            if not self.SAP_BEARER_TOKEN:
                raise ValueError(
                    "SAP_BEARER_TOKEN is required when SAP_MODE=real and SAP_AUTH_TYPE=bearer"
                )
        return self

    @property
    def allowed_mime_types(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
