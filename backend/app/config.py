from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    keitaro_base_url: str = "https://keitaro-for-tests.etolegko.com/admin_api/v1"
    keitaro_api_key: str = ""
    database_url: str = "sqlite:///database/app.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
