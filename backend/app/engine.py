
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Tuple

# Canonical shift timings per spec (simplified; production should read from config)
SHIFT_DEFS = {
    ("base", "Mon-Thu"): (time(9,0), time(17,0)),
    ("base", "Fri"): (time(9,0), time(16,0)),
    ("day_call", "Mon-Thu"): (time(9,0), time(17,0)),
    ("day_call", "Fri"): (time(9,0), time(13,0)),
    ("night_call", "Mon-Thu"): (time(17,0), time(9,0)),
    ("night_call", "Fri"): (time(13,0), time(11,0)),   # to Sat
    ("night_call", "Sat"): (time(11,0), time(10,0)),   # to Sun
    ("night_call", "Sun"): (time(10,0), time(9,0)),    # to Mon
}

PROTECTED_TEACHING = (time(14,0), time(16,30))  # Wednesday
HANDOVER_BLOCKS = [(time(16,30), time(17,0)), (time(9,0), time(9,30))]

def ewtd_check(daily_records: List[Tuple[datetime, datetime, str]]) -> Dict[str, bool]:
    """Basic EWTD (European Working Time Directive) checks.
    - duty length <= 24h
    - daily rest >= 11h within any 24h
    - weekly rest >= 24h (simplified)
    - average 48h/week (rolling) — stub
    """
    ok = True
    reasons = []

    for start, end, t in daily_records:
        duration = (end - start).total_seconds() / 3600.0
        if duration > 24.0:
            ok = False
            reasons.append(f"Duty exceeds 24h: {duration:.1f}h")

    # NOTE: Full rest and rolling averages require timeline accumulation — stubbed
    return {"ok": ok, "reasons": reasons}

def fairness_score(assignments: List[Tuple[int, float]]) -> float:
    """Very simple fairness proxy: stddev of on‑call hours per user (lower is better)."""
    import statistics
    hours = [h for _, h in assignments] or [0.0]
    return statistics.pstdev(hours)
