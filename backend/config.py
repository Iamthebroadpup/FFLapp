from pydantic import BaseSettings

class Settings(BaseSettings):
    FANTASY_NERDS_API_KEY: str = "TEST"  # replaced by Codespaces secret in prod
    CORS_ORIGINS: list[str] = ["*"]      # tighten later

settings = Settings()
