from typing import Protocol, Iterable
from dataclasses import dataclass

@dataclass
class DatedWindow:
    date: str
    start: str
    end: str
    tags: list[str]
    source: str  # 'core' | 'activity:GroupName' | 'assignment'

class ActivityProvider(Protocol):
    def windows_for_post(self, post_id: int, month: int, year: int) -> Iterable[DatedWindow]: ...

class AssignmentSink(Protocol):
    def preview(self, allocations: list[DatedWindow]) -> dict: ...
    def persist(self, allocations: list[DatedWindow]) -> dict: ...
