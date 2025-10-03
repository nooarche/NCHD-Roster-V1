from pydantic import BaseModel
from typing import Optional, List, Dict, Any

Time = str
TimeWindow = list[Time]

class ActivityBase(BaseModel):
    name: str
    kind: str               # "weekly" | "one_off"
    pattern: Dict[str, Any] # see pattern spec

class ActivityCreate(BaseModel):
    name: str
    kind: str
    pattern: Dict[str, Any] = {}

class ActivityOut(ActivityCreate):
    id: int
    group_id: int
    class Config:
        from_attributes = True

class GroupCreate(BaseModel):
    name: str
    kind: str
    rules: Dict[str, Any] = {}

class GroupOut(GroupCreate):
    id: int
    activities: List[ActivityOut] = []
    class Config:
        from_attributes = True

class ActivityCreate(ActivityBase):
    pass

class ActivityOut(ActivityBase):
    id: int
    group_id: int
    class Config:
        from_attributes = True

class GroupBase(BaseModel):
    name: str
    kind: str               # e.g. "on_call_pool" | "protected_teaching" | "clinic_team"
    rules: Dict[str, Any] = {}

class GroupCreate(GroupBase):
    pass

class GroupOut(GroupBase):
    id: int
    activities: List[ActivityOut] = []
    class Config:
        from_attributes = True

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

class GroupCreate(GroupBase): 
    pass
    
class GroupUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None

class GroupOut(GroupBase):
    id: int
    class Config:
        from_attributes = True

class GroupRead(GroupBase):
    id: int
