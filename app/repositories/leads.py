import json
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_lead(
    db: Session,
    creator_id: str,
    brand_name: Optional[str],
    brand_email: Optional[str],
    budget: Optional[float],
    custom_responses: dict[str, Any],
) -> dict[str, Any]:
    row = (
        db.execute(
            text(
                """
                INSERT INTO public.leads
                    (creator_id, brand_name, brand_email, budget, custom_responses, status)
                VALUES
                    (:creator_id, :brand_name, :brand_email, :budget,
                     CAST(:custom_responses AS jsonb), 'pending')
                RETURNING id, brand_name, brand_email, budget, custom_responses, status, created_at
                """
            ),
            {
                "creator_id": creator_id,
                "brand_name": brand_name,
                "brand_email": brand_email,
                "budget": budget,
                "custom_responses": json.dumps(custom_responses),
            },
        )
        .mappings()
        .first()
    )
    db.commit()
    return dict(row)


def get_leads_page(
    db: Session,
    creator_id: str,
    status: Optional[str],
    page: int,
    page_size: int,
    search: Optional[str],
) -> tuple[list[dict[str, Any]], int]:
    conditions = ["creator_id = :creator_id"]
    params: dict[str, Any] = {"creator_id": creator_id}

    if status:
        conditions.append("status = :status")
        params["status"] = status

    if search:
        conditions.append(
            "(LOWER(brand_name) LIKE :search OR LOWER(brand_email) LIKE :search)"
        )
        params["search"] = f"%{search.lower()}%"

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = (
        db.execute(
            text(
                f"""
                SELECT id, brand_name, brand_email, budget, custom_responses, status, created_at
                FROM public.leads
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    total: int = db.execute(
        text(f"SELECT COUNT(*) FROM public.leads WHERE {where}"),
        count_params,
    ).scalar_one()

    return [dict(r) for r in rows], total


def set_lead_status(
    db: Session,
    lead_id: str,
    creator_id: str,
    status: str,
) -> bool:
    result = db.execute(
        text(
            """
            UPDATE public.leads
            SET status = :status
            WHERE id = :lead_id AND creator_id = :creator_id
            """
        ),
        {"status": status, "lead_id": lead_id, "creator_id": creator_id},
    )
    db.commit()
    return result.rowcount > 0
