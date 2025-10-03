from pydantic import BaseModel
from typing import Literal, Optional

Time = str
TimeWindow = list[Time]

class WeeklyPattern(BaseModel):
    kind: Literal["weekly"] = "weekly"
    weekday: Literal["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    window: TimeWindow

class OneoffPattern(BaseModel):
    kind: Literal["oneoff"] = "oneoff"
    date: str
    window: TimeWindow

class Activity(BaseModel):
    name: str
    tags: list[Literal["clinic","opd","teaching","supervision","meeting","other"]]
    pattern: WeeklyPattern | OneoffPattern
    site: Optional[str] = None
    requires_supervisor: bool = False

class GroupBase(BaseModel):
    name: str
    kind: Literal["on_call_pool","teaching_block","team","site_rule","other"]
    rules: dict = {}
    activities: list[Activity] = []

class GroupCreate(GroupBase): ...
class GroupUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[Literal["on_call_pool","teaching_block","team","site_rule","other"]] = None
    rules: Optional[dict] = None
    activities: Optional[list[Activity]] = None

class GroupRead(GroupBase):
    id: int
