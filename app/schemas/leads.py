from typing import Any, Optional

from pydantic import BaseModel, Field

VALID_STATUS_KEYS = frozenset({"pending", "negotiating", "completed", "rejected"})


class SubmitLeadRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    custom_responses: dict[str, Any]


class LeadItem(BaseModel):
    id: str
    brand_name: Optional[str] = None
    brand_email: Optional[str] = None
    budget: Optional[float] = None
    custom_responses: dict[str, Any]
    status: str
    created_at: str


class LeadsPageResponse(BaseModel):
    items: list[LeadItem]
    total: int
    page: int
    page_size: int
    minimum_budget: Optional[int] = None
    currency: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str
