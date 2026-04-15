from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_user_by_id(db: Session, user_id: str) -> Optional[dict[str, Any]]:
    return (
        db.execute(
            text(
                """
                SELECT id, email, display_name, slug, avatar_url, created_at
                FROM public.users
                WHERE id = :id
                LIMIT 1
                """
            ),
            {"id": user_id},
        )
        .mappings()
        .first()
    )


def upsert_user_from_auth_claims(db: Session, user_id: str, email: str) -> None:
    db.execute(
        text(
            """
            INSERT INTO public.users (id, email, slug)
            VALUES (:id, :email, :slug)
            ON CONFLICT (id) DO UPDATE
            SET email = EXCLUDED.email
            """
        ),
        {
            "id": user_id,
            "email": email,
            "slug": f"u-{user_id}",
        },
    )
    db.commit()


def slug_exists_for_other_user(db: Session, slug: str, user_id: str) -> bool:
    row = db.execute(
        text("SELECT id FROM public.users WHERE slug = :slug LIMIT 1"),
        {"slug": slug},
    ).first()
    return bool(row and str(row[0]) != user_id)


def update_profile(
    db: Session, user_id: str, display_name: str, slug: str, avatar_url: Optional[str]
) -> None:
    db.execute(
        text(
            """
            UPDATE public.users
            SET display_name = :display_name,
                slug = :slug,
                avatar_url = :avatar_url
            WHERE id = :id
            """
        ),
        {
            "display_name": display_name,
            "slug": slug,
            "avatar_url": avatar_url,
            "id": user_id,
        },
    )
    db.commit()


def is_slug_available(db: Session, slug: str) -> bool:
    result = db.execute(
        text("SELECT 1 FROM public.users WHERE slug = :slug LIMIT 1"),
        {"slug": slug},
    ).first()
    return result is None
