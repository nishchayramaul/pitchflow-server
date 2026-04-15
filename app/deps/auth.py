import logging
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWKClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.config import settings
from app.repositories.users import get_user_by_id, upsert_user_from_auth_claims

bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
jwks_client = PyJWKClient(f"{settings.get_supabase_url()}/auth/v1/.well-known/jwks.json")
ALLOWED_ALGORITHMS = ["RS256", "ES256", "ES384", "RS384"]


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            audience=settings.supabase_jwt_audience,
            issuer=settings.get_supabase_issuer(),
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except InvalidTokenError as exc:
        logger.warning("JWT claims validation failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    except Exception as exc:
        logger.warning("JWT validation dependency failure: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user_by_id(db, user_id)
    if not user:
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        upsert_user_from_auth_claims(db, user_id, email)
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {
        "id": str(user["id"]),
        "email": str(user["email"]),
        "claims": payload,
    }
