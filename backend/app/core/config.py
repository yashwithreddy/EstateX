from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EstateX API"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/estatex",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )

    jwt_secret_key: str = Field(
        default="change-me",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    uploads_dir: str = "uploads"

    blockchain_enabled: bool = False
    blockchain_client_script: str = "../blockchain/scripts/estatexClient.js"
    chain_rpc_url: str = "http://127.0.0.1:8545"
    chain_private_key: str = ""
    chain_contract_address: str = ""


settings = Settings()


def cors_origins_list() -> list[str]:
    defaults = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    }
    configured = {origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()}
    return sorted(defaults.union(configured))
