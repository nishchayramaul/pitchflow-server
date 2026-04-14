from collections.abc import Generator
import logging
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base

logger = logging.getLogger(__name__)


def _build_engine():
    try:
        database_url = settings.get_database_url()
    except ValueError:
        logger.exception("Database configuration invalid. Provide DATABASE_URL.")
        raise

    parsed = urlparse(database_url)
    logger.info(
        "Initializing database engine for host=%s port=%s db=%s",
        parsed.hostname,
        parsed.port,
        parsed.path.lstrip("/"),
    )

    try:
        return create_engine(database_url, pool_pre_ping=True)
    except Exception:
        logger.exception(
            "Failed to initialize database engine. Check database credentials, "
            "driver, sslmode, and DNS/network access."
        )
        raise


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_db_schema() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
