from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "squadron-ops-demo-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    demo_password: str = "demo1234"
    # When true, require_roles authenticates only (open ACL for portfolio demos).
    # Env: DEMO_OPEN_RBAC=true|false
    demo_open_rbac: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()