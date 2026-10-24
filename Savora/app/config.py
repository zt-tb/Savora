from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    admin_id: int
    api_id: int
    api_hash: str
    database_url: str
    redis_url: str
    session_encryption_key: str

    downloader_session: str | None = None

    animated_emoji: bool = True

    vip_stars_d1: int = 50
    vip_stars_d7: int = 250
    vip_stars_d30: int = 700

    download_workers: int = 2


settings = Settings()
