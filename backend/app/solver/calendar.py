from typing import Iterable
from .interfaces import DatedWindow

def merge_baseline(core: Iterable[DatedWindow], acts: Iterable[DatedWindow]) -> list[DatedWindow]:
    return list(core) + list(acts)
