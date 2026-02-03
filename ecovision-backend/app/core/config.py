from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # one week

    # optional keys used for DXF AI / MNML integrations
    dxf_ai_api_key: Optional[str] = None
    mnml_api_key: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
