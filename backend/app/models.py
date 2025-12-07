from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


# Inventor models
class InventorBase(BaseModel):
    name: str
    email: str | None = None


class InventorCreate(InventorBase):
    pass


class Inventor(InventorBase):
    id: UUID
    disclosure_id: UUID
    created_at: datetime


# Disclosure models
class DisclosureBase(BaseModel):
    title: str
    description: str
    key_differences: str


class DisclosureCreate(DisclosureBase):
    inventors: list[InventorCreate] = []


class DisclosureUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    key_differences: str | None = None
    status: str | None = None
    review_notes: str | None = None


class Disclosure(DisclosureBase):
    id: UUID
    docket_number: str
    status: str
    review_notes: str | None = None
    original_filename: str | None
    created_at: datetime
    updated_at: datetime


class StatusHistoryEntry(BaseModel):
    id: UUID
    disclosure_id: UUID
    status: str
    changed_at: datetime


class DisclosureWithInventors(Disclosure):
    inventors: list[Inventor] = []
    status_history: list[StatusHistoryEntry] = []


# Response for upload
class UploadResponse(BaseModel):
    disclosure: DisclosureWithInventors
    message: str


# Error response
class ErrorResponse(BaseModel):
    detail: str
