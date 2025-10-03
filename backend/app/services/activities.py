from datetime import date, timedelta
from typing import Iterable
from ..solver.interfaces import DatedWindow

WEEKDAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def expand_weekly(month: int, year: int, weekday: str, window: list[str], tags: list[str], source: str) -> Iterable[DatedWindow]:
    d = date(year, month, 1)
    while d.month == month:
        if WEEKDAYS[d.weekday()] == weekday:
            yield DatedWindow(date=d.isoformat(), start=window[0], end=window[1], tags=tags, source=source)
        d += timedelta(days=1)
