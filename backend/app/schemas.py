
from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, Any

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

class RotaSlotOut(BaseModel):
    id: int
    user_id: Optional[int]
    post_id: Optional[int]
    start: datetime
    end: datetime
    type: str
    labels: Optional[Any]
    class Config:
        from_attributes = True
