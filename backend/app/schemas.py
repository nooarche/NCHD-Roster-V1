from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date, time
from typing import Optional, List, Any

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

from typing import List, Optional

class RosterBuildRequest(BaseModel):
    year: int
    month: int                     # 1..12
    day_calls_per_day: int = 0     # keep 0 for now; we focus on nights
    night_calls_per_day: int = 1
    pool_roles: List[str] = ["nchd"]  # which roles are eligible (default NCHDs)

class RosterBuildResult(BaseModel):
    created_slots: int

class RosterUpdateRequest(BaseModel):
    slot_id: Optional[int] = None
    user_id: Optional[int] = None

class PostIn(BaseModel):
    title: str
    opd_day: Optional[str] = None

class PostOut(PostIn):
    id: int
    class Config: from_attributes = True

class TeamIn(BaseModel):
    name: str
    supervisor_id: Optional[int] = None

class TeamOut(TeamIn):
    id: int
    class Config: from_attributes = True

class ContractIn(BaseModel):
    user_id: int
    post_id: int
    team_id: Optional[int] = None
    start: date
    end: Optional[date] = None

class ContractOut(ContractIn):
    id: int
    class Config: from_attributes = True

class TeamMemberIn(BaseModel):
    user_id: int
    role: str = "nchd"

class TeamMemberOut(TeamMemberIn):
    id: int
    team_id: int
    class Config: from_attributes = True

class CoreHoursProfileIn(BaseModel):
    name: str
    weekly_hours: int
    policy_json: dict = Field(default_factory=dict)

class CoreHoursProfileOut(CoreHoursProfileIn):
    id: int
    class Config: from_attributes = True

class CoreHoursOverrideIn(BaseModel):
    user_id: int
    start: date
    end: Optional[date] = None
    weekly_hours: int

class CoreHoursOverrideOut(CoreHoursOverrideIn):
    id: int
    class Config: from_attributes = True

class OPDIn(BaseModel):
    user_id: int
    day_of_week: int
    start_time: time
    end_time: time
    within_core: bool = True

class OPDOut(OPDIn):
    id: int
    class Config: from_attributes = True

class SupervisionIn(BaseModel):
    supervisor_id: int
    nchd_id: int
    day_of_week: int
    start_time: time
    end_time: time

class SupervisionOut(SupervisionIn):
    id: int
    class Config: from_attributes = True

class OnCallAssignIn(BaseModel):
    user_id: int
    start: datetime
    end: datetime
    type: str = "night_call"
    post_id: Optional[int] = None  # default to first post if none

class AutofillByPostIn(BaseModel):
    post_id: int
    year: int
    month: int
