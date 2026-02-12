"""
HireMate Backend Configuration

Loads settings from environment variables with validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

# Backend root (parent of app/) so .env is always loaded from backend/
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "HireMate Backend"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "hiremate"

    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Assessment Token
    assessment_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000"

    # Idle Detection
    idle_threshold_ms: int = 5000

    # Development: when True, recruiter endpoints accept requests without JWT
    # by using the first active user (e.g. seeded admin). Disable in production.
    dev_mode: bool = False

    # Demo auth: when Bearer token equals this string, backend uses first active user (for testing without login UI).
    # Set empty in production to disable. Example: DEMO_AUTH_TOKEN=demo
    demo_auth_token: str = "demo"

    # Resume upload: directory to store uploaded files (relative to backend root or absolute)
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    # Redis (for Celery task queue)
    redis_url: str = "redis://localhost:6379/0"

    # AI Services
    groq_api_key: str = ""
    gemini_api_key: str = ""
    ai_model_8b: str = "llama-3.1-8b-instant"
    ai_model_70b: str = "llama-3.3-70b-versatile"
    ai_model_120b: str = "openai/gpt-oss-120b"

    # Email Service (Resend)
    resend_api_key: str = ""
    email_from_address: str = "HireMate <onboarding@resend.dev>"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = str(_BACKEND_ROOT / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
