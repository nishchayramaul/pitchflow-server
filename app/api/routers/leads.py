from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps.auth import get_current_user
from app.repositories.leads import get_all_leads
from app.repositories.users import get_user_by_id
from app.schemas.leads import LeadsPageResponse, SubmitLeadRequest, UpdateStatusRequest
from app.services.export_service import build_leads_excel
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


@router.get("/export")
def export_leads(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> Response:
    creator_id = user["id"]
    leads = get_all_leads(db, creator_id, status)

    profile = get_user_by_id(db, creator_id)
    currency = (profile.get("currency") if profile else None) or "USD"
    form_schema = profile.get("form_schema") if profile else None
    creator_email = user.get("email", "")

    xlsx_bytes = build_leads_excel(
        leads=leads,
        form_schema=form_schema if isinstance(form_schema, list) else None,
        currency=currency,
        creator_email=creator_email,
    )

    filename = quote("pitchflow_leads.xlsx")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.patch("/{lead_id}/status")
def update_lead_status(
    lead_id: str,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    return patch_lead_status(db, user, lead_id, payload)
