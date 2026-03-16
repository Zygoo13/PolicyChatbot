from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
