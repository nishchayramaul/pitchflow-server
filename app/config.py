from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlsplit


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PitchFlow API"
    frontend_origins: str = "http://localhost:4200"
    frontend_url: str = "http://localhost:4200"

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]

    # ── SMTP ──────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""          # display "From" address; falls back to smtp_user
    smtp_use_tls: bool = True    # True = STARTTLS (587) or SMTPS when port=465

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    database_url: str = Field(default="")
    supabase_url: str = ""
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_issuer: str = ""

    def get_database_url(self) -> str:
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")

        normalized_url = self.database_url.strip()
        parsed = urlsplit(normalized_url)
        if parsed.netloc.count("@") > 1:
            raise ValueError(
                "DATABASE_URL appears malformed: URL credentials contain unescaped "
                "special characters. URL-encode password characters like '@' as '%40'."
            )

        if normalized_url.startswith("postgresql://"):
            normalized_url = normalized_url.replace("postgresql://", "postgresql+psycopg://", 1)

        return normalized_url

    def get_supabase_url(self) -> str:
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required for JWKS token verification")
        return self.supabase_url.rstrip("/")

    def get_supabase_issuer(self) -> str:
        if self.supabase_jwt_issuer:
            return self.supabase_jwt_issuer.rstrip("/")
        return f"{self.get_supabase_url()}/auth/v1"


settings = Settings()
