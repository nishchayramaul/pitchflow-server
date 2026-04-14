from typing import Optional

from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=3, max_length=32)
    avatar_url: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    slug: Optional[str] = None
    avatar_url: Optional[str] = None
