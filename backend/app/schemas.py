
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

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

from typing import List

class OnCallEvent(BaseModel):
    start: datetime
    end: datetime
    type: str
    user_id: int
    user_name: str

class ValidationIssue(BaseModel):
    user_id: int
    user_name: str
    slot_id: int
    message: str

class ValidationReport(BaseModel):
    ok: bool
    issues: List[ValidationIssue]
