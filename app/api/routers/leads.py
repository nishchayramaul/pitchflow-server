from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps.auth import get_current_user
from app.schemas.leads import LeadsPageResponse, SubmitLeadRequest, UpdateStatusRequest
from app.services.leads_service import list_leads, patch_lead_status, submit_lead

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("", status_code=201)
def post_lead(
    payload: SubmitLeadRequest,
    db: Session = Depends(get_db),
) -> dict:
    return submit_lead(db, payload)


@router.get("", response_model=LeadsPageResponse)
def get_leads(
    page: int = 1,
    page_size: int = 200,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> LeadsPageResponse:
    return list_leads(db, user, page, page_size, status, search)


@router.patch("/{lead_id}/status")
def update_lead_status(
    lead_id: str,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    return patch_lead_status(db, user, lead_id, payload)
