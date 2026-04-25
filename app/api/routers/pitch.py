from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.profile import PublicPitchFormResponse
from app.services.onboarding_service import get_public_pitch_form

router = APIRouter(prefix="/api/pitch", tags=["pitch"])


@router.get("/{slug}", response_model=PublicPitchFormResponse)
def get_pitch_form(slug: str, db: Session = Depends(get_db)) -> PublicPitchFormResponse:
    return get_public_pitch_form(db, slug)
