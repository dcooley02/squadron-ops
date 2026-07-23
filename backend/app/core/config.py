from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known demo defaults — fine for local portfolio demos; rejected when ENVIRONMENT=production.
_DEMO_SECRET_KEY = "squadron-ops-demo-secret-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # development (default) | production
    environment: str = "development"

    secret_key: str = _DEMO_SECRET_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    demo_password: str = "demo1234"
    # When true, require_roles authenticates only (open ACL for portfolio demos).
    # Env: DEMO_OPEN_RBAC=true|false
    demo_open_rbac: bool = False

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, v: object) -> str:
        if v is None or v == "":
            return "development"
        return str(v).strip().lower()

    @model_validator(mode="after")
    def reject_demo_secrets_in_production(self) -> "Settings":
        if self.environment != "production":
            return self
        if self.secret_key == _DEMO_SECRET_KEY or not self.secret_key.strip():
            raise ValueError(
                "ENVIRONMENT=production requires a non-default SECRET_KEY. "
                "Set SECRET_KEY to a long random string (e.g. openssl rand -hex 32)."
            )
        if self.demo_open_rbac:
            raise ValueError(
                "ENVIRONMENT=production cannot use DEMO_OPEN_RBAC=true. "
                "Disable open ACL for production-shaped deployments."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
