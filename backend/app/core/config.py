from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/placement_portal"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/placement_portal"
    secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "placement-portal"

    use_local_storage: bool = True
    local_storage_path: str = "./uploads"

    max_upload_size_mb: int = 5
    seed_demo_data: bool = True

    # Student self-registration disabled until college email DB is available
    allow_student_registration: bool = False

    # Campus-only access. Centre = IIPS DAVV map pin. Set GEOFENCE_ENABLED=false to work from outside campus.
    geofence_enabled: bool = True
    campus_latitude: float = 22.6884251
    campus_longitude: float = 75.876705
    campus_radius_m: int = 500
    campus_pass_minutes: int = 15

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
