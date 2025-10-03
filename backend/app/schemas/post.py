from pydantic import BaseModel, Field
from typing import Literal, Optional

Time = str
TimeWindow = list[Time]
TimeWindows = list[TimeWindow]

class DayCall(BaseModel):
    windows: TimeWindows
    allowed_days: list[Literal["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]] = ["Mon","Tue","Wed","Thu","Fri"]
    must_be_on_site: bool = True
    location_required: Optional[str] = "Newcastle Hospital"

class NightCall(BaseModel):
    windows: TimeWindows
    cap_per_month: int = 7
    min_rest_hours: int = 11

class PostCall(BaseModel):
    rest_hours: int = 11
    suppress_next_day_core: Literal["auto","none","entire_day"] = "auto"
    in_lieu_core: bool = True
    forbid_rest_on_activity_tags: list[Literal["clinic","opd","teaching","supervision"]] = ["clinic","opd"]
    allow_with_supervisor_override: bool = True

class CallPolicy(BaseModel):
    participates_in_call: bool = True
    role: str = "NCHD"
    day_call: Optional[DayCall] = None
    night_call: Optional[NightCall] = None
    post_call: Optional[PostCall] = None

class EWTD(BaseModel):
    max_hours_per_week: int = 48
    max_consecutive_working_days: int = 6
    min_daily_rest_hours: int = 11
    min_weekly_rest_hours: int = 24

class Fairness(BaseModel):
    balance_unsocial_hours: bool = True
    balance_total_hours: bool = True
    weight_unsocial_hours: float = 1.0
    weight_total_hours: float = 0.5

class Constraints(BaseModel):
    ewtd: EWTD = EWTD()
    fairness: Fairness = Fairness()
    hard_rules: list[str] = ["no_rest_on_activity:clinic","no_rest_on_activity:opd"]

class CorePolicy(BaseModel):
    worked_anyway: bool = True
    overridden_by: list[str] = ["night_call","leave","public_holiday"]

CoreHours = dict[str, TimeWindows | CorePolicy]  # {"Mon":[["09:00","17:00"]], "policy":{...}}

class PostBase(BaseModel):
    title: str
    site: Optional[str] = None
    grade: Optional[str] = None
    fte: float = 1.0
    status: Literal["ACTIVE_ROSTERABLE","VACANT_UNROSTERABLE","INACTIVE"]
    core_hours: Optional[CoreHours] = None
    eligibility: Optional[dict] = Field(default_factory=dict)
    constraints: Optional[Constraints] = None
    group_ids: list[int] = []
    notes: Optional[str] = None

class PostCreate(PostBase): ...
class PostUpdate(PostBase): ...

class PostRead(PostBase):
    id: int
