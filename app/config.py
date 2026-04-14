from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PitchFlow API"
    frontend_origin: str = "http://localhost:4200"
    database_url: str = Field(default="")
    supabase_jwt_secret: str = ""
    supabase_jwt_algorithm: str = "HS256"
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_issuer: str = ""

    def get_database_url(self) -> str:
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
        return self.database_url


settings = Settings()
