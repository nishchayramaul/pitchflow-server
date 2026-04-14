import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.users import (
    get_user_by_id,
    is_slug_available,
    slug_exists_for_other_user,
    update_profile,
)
from app.schemas.profile import UpdateProfileRequest, UserProfileResponse

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
    )
