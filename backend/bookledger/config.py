from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOOKLEDGER_", extra="ignore")

    config_dir: Path = Path("/config")
    database_url_override: str | None = None

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        self.config_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.config_dir / 'bookledger.db'}"


settings = Settings()
