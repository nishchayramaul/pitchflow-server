import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.users import (
    get_user_by_id,
    get_user_by_slug,
    is_slug_available,
    slug_exists_for_other_user,
    update_currency,
    update_form_schema,
    update_minimum_budget,
    update_profile,
)
from app.schemas.profile import (
    CurrencyUpdateRequest,
    FormSchemaUpdateRequest,
    MinimumBudgetUpdateRequest,
    PublicPitchFormResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)

SLUG_PATTERN = re.compile(r"^[a-z0-9-]{3,32}$")


def assert_valid_slug(slug: str) -> None:
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=400, detail="Slug format is invalid")


def check_slug_availability(db: Session, slug: str) -> dict[str, bool]:
    assert_valid_slug(slug)
    return {"is_available": is_slug_available(db, slug)}


def update_user_profile(
    db: Session, user_id: str, payload: UpdateProfileRequest
) -> dict[str, str]:
    assert_valid_slug(payload.slug)
    if slug_exists_for_other_user(db, payload.slug, user_id):
        raise HTTPException(status_code=409, detail="Slug is already taken")

    update_profile(
        db=db,
        user_id=user_id,
        display_name=payload.display_name,
        slug=payload.slug,
        avatar_url=payload.avatar_url,
    )
    return {"message": f"Link generated: pitchflow.in/{payload.slug}"}


def get_public_pitch_form(db: Session, slug: str) -> PublicPitchFormResponse:
    user = get_user_by_slug(db, slug)
    if not user:
        raise HTTPException(status_code=404, detail="Creator not found")
    return PublicPitchFormResponse(
        display_name=user["display_name"] or slug,
        form_schema=user["form_schema"] or [],
    )


def save_form_schema(
    db: Session, user_id: str, user_role: str, payload: FormSchemaUpdateRequest
) -> dict[str, str]:
    if user_role == "team_member":
        raise HTTPException(status_code=403, detail="Team members cannot modify the form schema")
    update_form_schema(db, user_id, payload.form_schema)
    return {"message": "Form schema saved"}


def save_minimum_budget(
    db: Session, user_id: str, payload: MinimumBudgetUpdateRequest
) -> dict[str, str]:
    update_minimum_budget(db, user_id, payload.minimum_budget)
    return {"message": "Minimum budget saved"}


def save_currency(
    db: Session, user_id: str, payload: CurrencyUpdateRequest
) -> dict[str, str]:
    update_currency(db, user_id, payload.currency)
    return {"message": "Currency saved"}


def get_current_profile(db: Session, user_id: str) -> UserProfileResponse:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return UserProfileResponse(
        id=str(user["id"]),
        email=str(user["email"]),
        display_name=user.get("display_name"),
        slug=user.get("slug"),
        avatar_url=user.get("avatar_url"),
        tier=user.get("tier"),
        role=user.get("role"),
        form_schema=user.get("form_schema"),
        minimum_budget=user.get("minimum_budget"),
        currency=user.get("currency"),
    )
