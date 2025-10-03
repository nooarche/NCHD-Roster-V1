from .interfaces import DatedWindow

def overlaps(a: DatedWindow, b: DatedWindow) -> bool:
    return (a.date == b.date) and not (a.end <= b.start or b.end <= a.start)

def forbid_rest_on_tag(rest_windows: list[DatedWindow], activities: list[DatedWindow], forbidden: set[str]) -> bool:
    for r in rest_windows:
        for act in activities:
            if forbidden.intersection(act.tags) and overlaps(r, act):
                return True
    return False
