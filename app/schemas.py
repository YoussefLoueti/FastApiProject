from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime

# === User Schemas ===

class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_default: bool
    can_delete: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# === Item Schemas ===

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float


class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: float
    owner_id: int
    is_default: bool
    can_delete: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === Combined Schemas ===

class UserWithItems(UserResponse):
    items: List[ItemResponse] = []  # 🟢 Correct way to include nested list


class ItemWithOwner(ItemResponse):
    owner: UserResponse  # 🟢 Owner is nested inside item


class StandardResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None
