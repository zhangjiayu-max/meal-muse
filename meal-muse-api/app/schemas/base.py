"""通用 Pydantic Schema"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    error: str
    code: str = ""
    detail: str = ""


class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None
