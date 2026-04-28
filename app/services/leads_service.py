from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.leads import get_leads_page, insert_lead, set_lead_status
from app.repositories.users import get_user_by_id, get_user_by_slug
from app.schemas.leads import (
    LeadItem,
    LeadsPageResponse,
    SubmitLeadRequest,
    UpdateStatusRequest,
    VALID_STATUS_KEYS,
)


def _coerce_float(val: Any) -> Optional[float]:
    try:
        return float(val) if val is not None and val != "" else None
    except (TypeError, ValueError):
        return None


def submit_lead(db: Session, payload: SubmitLeadRequest) -> dict[str, str]:
    creator = get_user_by_slug(db, payload.slug)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    resp = payload.custom_responses
    brand_name = str(resp.get("brand_name", "")).strip() or None
    brand_email = str(resp.get("brand_email", "")).strip() or None
    budget = _coerce_float(resp.get("budget"))

    insert_lead(
        db=db,
        creator_id=str(creator["id"]),
        brand_name=brand_name,
        brand_email=brand_email,
        budget=budget,
        custom_responses=resp,
    )
    return {"message": "Pitch submitted successfully"}


def list_leads(
    db: Session,
    user: dict[str, Any],
    page: int,
    page_size: int,
    status: Optional[str],
    search: Optional[str],
) -> LeadsPageResponse:
    if page < 1:
        page = 1
    page_size = max(1, min(page_size, 200))

    if status and status not in VALID_STATUS_KEYS:
        raise HTTPException(status_code=400, detail=f"Invalid status key: {status}")

    creator_id = user["id"]
    rows, total = get_leads_page(
        db=db,
        creator_id=creator_id,
        status=status,
        page=page,
        page_size=page_size,
        search=search,
    )

    profile = get_user_by_id(db, creator_id)
    minimum_budget = profile.get("minimum_budget") if profile else None
    currency = profile.get("currency") if profile else "USD"

    items = [
        LeadItem(
            id=str(r["id"]),
            brand_name=r.get("brand_name"),
            brand_email=r.get("brand_email"),
            budget=float(r["budget"]) if r.get("budget") is not None else None,
            custom_responses=r.get("custom_responses") or {},
            status=r["status"],
            created_at=r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
        )
        for r in rows
    ]

    return LeadsPageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        minimum_budget=minimum_budget,
        currency=currency,
    )


def patch_lead_status(
    db: Session,
    user: dict[str, Any],
    lead_id: str,
    payload: UpdateStatusRequest,
) -> dict[str, str]:
    if payload.status not in VALID_STATUS_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid keys: {sorted(VALID_STATUS_KEYS)}",
        )

    updated = set_lead_status(
        db=db,
        lead_id=lead_id,
        creator_id=user["id"],
        status=payload.status,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Status updated"}
