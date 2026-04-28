from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any

from app.db import get_db
from app.deps.auth import get_current_user, get_current_user_full
from app.schemas.profile import CurrencyUpdateRequest, FormSchemaUpdateRequest, MinimumBudgetUpdateRequest, UpdateProfileRequest, UserProfileResponse
from app.services.onboarding_service import (
    check_slug_availability,
    get_current_profile,
    save_currency,
    save_form_schema,
    save_minimum_budget,
    update_user_profile,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/check-slug/{slug}")
def check_slug(slug: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    return check_slug_availability(db, slug)


@router.get("/me", response_model=UserProfileResponse)
def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    return get_current_profile(db, current_user["id"])


@router.put("/profile")
def update_profile(
    payload: UpdateProfileRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return update_user_profile(db, current_user["id"], payload)


@router.patch("/form-schema")
def update_form_schema(
    payload: FormSchemaUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user_full),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return save_form_schema(db, current_user["id"], current_user["role"], payload)


@router.patch("/minimum-budget")
def update_minimum_budget(
    payload: MinimumBudgetUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return save_minimum_budget(db, current_user["id"], payload)


@router.patch("/currency")
def update_currency(
    payload: CurrencyUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return save_currency(db, current_user["id"], payload)
