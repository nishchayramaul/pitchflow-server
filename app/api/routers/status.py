from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.onboarding_service import check_slug_availability

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/status")
def get_status(creator_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    return check_slug_availability(db, creator_id)