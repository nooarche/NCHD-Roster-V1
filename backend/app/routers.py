from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import and_

from .db import get_db
from . import models, schemas

api = APIRouter()



@api.get("/users")
def list_users(db: Session = Depends(get_db)) -> List[dict]:
    # TEMP stub so the UI doesn't 404; replace with real query later.
    return []

#@api.get("/users", response_model=List[schemas.UserOut])
#def list_users(db: Session = Depends(get_db)):
#    return db.query(models.User).all()

@api.get("/health")
def health():
    return {"status": "ok"}



@api.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    u = models.User(name=user.name, email=user.email, role=user.role)
    db.add(u); db.commit(); db.refresh(u)
    return u

# Example action endpoints (roster build, refresh) — stubs

@api.post("/actions/roster-refresh")
def roster_refresh(db: Session = Depends(get_db)):
    return {"status": "ok", "message": "Roster refresh stubbed."}

@api.patch("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, patch: schemas.UserUpdate, db: Session = Depends(get_db)):
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if patch.name is not None: u.name = patch.name
    if patch.email is not None: u.email = patch.email
    if patch.role is not None: u.role = patch.role
    db.commit(); db.refresh(u)
    return u

@api.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u); db.commit()
    return {"status": "deleted", "id": user_id}

@api.get("/oncall/month", response_model=List[schemas.OnCallEvent])
def oncall_month(year: int, month: int, db: Session = Depends(get_db)):
    first = datetime(year, month, 1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    q = (
        db.query(models.RotaSlot, models.User.name)
          .join(models.User, models.User.id == models.RotaSlot.user_id, isouter=True)
          .filter(models.RotaSlot.start >= first)
          .filter(models.RotaSlot.start < next_month)
          .filter(models.RotaSlot.type.in_(["night_call", "day_call"]))
          .order_by(models.RotaSlot.start.asc())
    )
    out = []
    for slot, uname in q.all():
        out.append(schemas.OnCallEvent(
            slot_id=slot.id,                 # ⬅️ now included
            start=slot.start, end=slot.end, type=slot.type,
            user_id=slot.user_id or 0, user_name=uname or "Unassigned"
        ))
    return out

# backend/app/routers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from . import models, schemas
from typing import List
from datetime import date

api = APIRouter()

# ... existing health, users, actions stubs ...

# POSTS
@api.get("/posts", response_model=List[schemas.PostOut])
def list_posts(db: Session = Depends(get_db)):
    return db.query(models.Post).all()

@api.post("/posts", response_model=schemas.PostOut)
def create_post(data: schemas.PostCreate, db: Session = Depends(get_db)):
    p = models.Post(**data.dict())
    db.add(p); db.commit(); db.refresh(p)
    return p

@api.get("/posts/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p: raise HTTPException(404, "Post not found")
    return p

@api.put("/posts/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, data: schemas.PostCreate, db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p: raise HTTPException(404, "Post not found")
    for k, v in data.dict().items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p

@api.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p: raise HTTPException(404, "Post not found")
    db.delete(p); db.commit()
    return {"status": "ok"}

# VACANCY WINDOWS
@api.get("/posts/{post_id}/vacancy", response_model=List[schemas.VacancyWindowOut])
def list_vacancy(post_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p: raise HTTPException(404, "Post not found")
    return db.query(models.VacancyWindow).filter_by(post_id=post_id).all()

@api.post("/posts/{post_id}/vacancy", response_model=schemas.VacancyWindowOut)
def add_vacancy(post_id: int, data: schemas.VacancyWindowCreate, db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p: raise HTTPException(404, "Post not found")
    vw = models.VacancyWindow(post_id=post_id, **data.dict())
    # basic guard: end >= start
    if vw.end_date and vw.end_date < vw.start_date:
        raise HTTPException(400, "end_date cannot be before start_date")
    db.add(vw); db.commit(); db.refresh(vw)
    return vw

@api.delete("/posts/{post_id}/vacancy/{vw_id}")
def delete_vacancy(post_id: int, vw_id: int, db: Session = Depends(get_db)):
    vw = db.query(models.VacancyWindow).get(vw_id)
    if not vw or vw.post_id != post_id:
        raise HTTPException(404, "Vacancy window not found")
    db.delete(vw); db.commit()
    return {"status": "ok"}

# QUICK FEASIBILITY PING (stub)
@api.get("/feasibility")
def feasibility(db: Session = Depends(get_db)):
    """
    Returns a coarse view: number of posts ACTIVE/ROSTERABLE vs. VACANT_UNROSTERABLE *today*.
    The real engine will replace this with full coverage/EWTD checks and 'first failing date'.
    """
    today = date.today()
    posts = db.query(models.Post).all()
    def is_unrosterable(p: models.Post) -> bool:
        if p.status == "VACANT_UNROSTERABLE": return True
        # any window marking today as UNROSTERABLE?
        for w in p.vacancy_windows:
            if w.status == "VACANT_UNROSTERABLE" and w.start_date <= today and (w.end_date is None or w.end_date >= today):
                return True
        return False
    unrosterable = sum(1 for p in posts if is_unrosterable(p))
    rosterable = len(posts) - unrosterable
    # naive locum signal (replace later)
    locum_required = rosterable < 1  # if you require coverage=1, tweak once service lines exist
    return {"date": str(today), "posts_total": len(posts), "rosterable": rosterable,
            "unrosterable": unrosterable, "locum_required": locum_required}

# start of /validate/rota
# We can add OPD/supervision collisions once those tables are populated.

@api.get("/validate/rota", response_model=schemas.ValidationReport)
def validate_rota(year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Runs policy-driven checks over a window (default = all future + current month).
    Returns a list of ValidationIssue {user_id, user_name, slot_id, message}.
    """
    from collections import defaultdict
    from sqlalchemy import and_
    import math

    # 1) Load policy (simple: first CoreHoursProfile or hard-coded defaults)
    policy = {
        "max_continuous_hours": 24,
        "min_daily_rest_hours": 11,
        "max_hours_per_7_days": 60,
        "max_consecutive_days": 6,
        "max_consecutive_nights": 3,
        "max_night_spread": 2,
        "require_one_night_per_post_per_day": True,
        "night_start": "17:00",
        "night_end": "09:00",
        "enforce_post_match_to_contract": True,
    }

    # 2) Window
    if year and month:
        first = datetime(year, month, 1)
        next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        slot_filter = and_(models.RotaSlot.start < next_month, models.RotaSlot.end > first)
    else:
        # default: current month
        today = datetime.utcnow().date().replace(day=1)
        first = datetime(today.year, today.month, 1)
        next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        slot_filter = and_(models.RotaSlot.start < next_month, models.RotaSlot.end > first)

    issues: list[schemas.ValidationIssue] = []

    # 3) Fetch slots (with users)
    slots = (
        db.query(models.RotaSlot, models.User.name)
          .join(models.User, models.User.id == models.RotaSlot.user_id, isouter=True)
          .filter(slot_filter)
          .order_by(models.RotaSlot.user_id.asc(), models.RotaSlot.start.asc())
          .all()
    )

    # Index by user
    by_user: dict[int, list[models.RotaSlot]] = defaultdict(list)
    for slot, _uname in slots:
        if slot.user_id:
            by_user[slot.user_id].append(slot)

    # 4) Basic integrity
    for slot, uname in slots:
        if slot.end <= slot.start:
            issues.append(_issue(slot, uname, "Slot end is not after start"))
    # overlaps
    for uid, arr in by_user.items():
        arr.sort(key=lambda s: s.start)
        for a, b in zip(arr, arr[1:]):
            if b.start < a.end:
                uname = db.query(models.User.name).filter(models.User.id==uid).scalar()
                issues.append(_issue(a, uname, "Overlapping assignment with next slot"))

    # 5) Continuous duty length
    for slot, uname in slots:
        hours = (slot.end - slot.start).total_seconds() / 3600.0
        if hours > policy["max_continuous_hours"]:
            issues.append(_issue(slot, uname, f"Duty exceeds {policy['max_continuous_hours']}h ({hours:.1f}h)"))

    # 6) Daily rest after duty
    for uid, arr in by_user.items():
        uname = db.query(models.User.name).filter(models.User.id==uid).scalar()
        arr.sort(key=lambda s: s.start)
        for a, b in zip(arr, arr[1:]):
            gap = (b.start - a.end).total_seconds() / 3600.0
            if gap < policy["min_daily_rest_hours"]:
                issues.append(_issue(a, uname, f"Rest gap {gap:.1f}h < {policy['min_daily_rest_hours']}h before next duty"))

    # 7) Max hours per 7 days (simple rolling)
    for uid, arr in by_user.items():
        uname = db.query(models.User.name).filter(models.User.id==uid).scalar()
        arr.sort(key=lambda s: s.start)
        for i in range(len(arr)):
            window_start = arr[i].start
            window_end = window_start + timedelta(days=7)
            total = 0.0
            for s in arr:
                if s.start < window_end and s.end > window_start:
                    total += (min(s.end, window_end) - max(s.start, window_start)).total_seconds()/3600.0
            if total > policy["max_hours_per_7_days"]:
                issues.append(_issue(arr[i], uname, f"Hours {total:.1f}h in 7 days > {policy['max_hours_per_7_days']}h"))

    # 8) Consecutive days / nights
    def is_night(s: models.RotaSlot): return s.type == "night_call"
    for uid, arr in by_user.items():
        uname = db.query(models.User.name).filter(models.User.id==uid).scalar()
        # consecutive days
        cons = 1
        for a, b in zip(arr, arr[1:]):
            if (b.start.date() - a.start.date()).days == 1:
                cons += 1
            else:
                cons = 1
            if cons > policy["max_consecutive_days"]:
                issues.append(_issue(b, uname, f"Consecutive days {cons} exceeds {policy['max_consecutive_days']}"))
        # consecutive nights
        nights = [s for s in arr if is_night(s)]
        cons_n = 1
        for a, b in zip(nights, nights[1:]):
            if (b.start.date() - a.start.date()).days == 1:
                cons_n += 1
            else:
                cons_n = 1
            if cons_n > policy["max_consecutive_nights"]:
                issues.append(_issue(b, uname, f"Consecutive nights {cons_n} exceeds {policy['max_consecutive_nights']}"))

    # 9) Exactly one night per post/day (if required)
    if policy["require_one_night_per_post_per_day"]:
        from collections import defaultdict
        per = defaultdict(list)  # (date, post_id) -> slots
        for slot, _uname in slots:
            if slot.type == "night_call":
                key = (slot.start.date(), slot.post_id)
                per[key].append(slot)
        # duplicates
        for key, arr in per.items():
            if len(arr) > 1:
                for s in arr[1:]:
                    uname = db.query(models.User.name).filter(models.User.id==s.user_id).scalar()
                    issues.append(_issue(s, uname, f"Multiple night_call for post {key[1]} on {key[0]}"))
        # missing coverage per post/day (optional: check against posts table)
        # If you want strict coverage, iterate posts and days in window and add a "missing" issue

    # 10) Contract window and post match
    for slot, uname in slots:
        if not slot.user_id:
            continue
        c = (db.query(models.Contract)
               .filter(models.Contract.user_id == slot.user_id)
               .filter(models.Contract.start <= slot.start.date())
               .filter((models.Contract.end == None) | (models.Contract.end >= slot.start.date()))
               .order_by(models.Contract.start.asc())
               .first())
        if not c:
            issues.append(_issue(slot, uname, "No active contract for user on this date"))
        else:
            if policy["enforce_post_match_to_contract"] and slot.post_id != c.post_id:
                issues.append(_issue(slot, uname, f"Post {slot.post_id} does not match contract post {c.post_id}"))

    return schemas.ValidationReport(ok=(len(issues) == 0), issues=issues)

def _issue(slot: "models.RotaSlot", uname: Optional[str], msg: str) -> schemas.ValidationIssue:
    return schemas.ValidationIssue(
        user_id=slot.user_id or 0,
        user_name=uname or "Unassigned",
        slot_id=slot.id or 0,
        message=msg,
    )
#end of /validate/rota


@api.post("/actions/roster-build", response_model=schemas.RosterBuildResult)
def roster_build(req: schemas.RosterBuildRequest, db: Session = Depends(get_db)):
    """
    Contracts-aware month builder:
      - For each day in the target month, compute eligible users = NCHDs with an active Contract on that date
      - Wipes existing night/day call in the window
      - Assigns 1 night_call per day, round-robin over that day's eligible pool
      - Uses the eligible user's contract.post_id for the created slot
    """
    first = datetime(req.year, req.month, 1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    # wipe existing calls in window
    db.query(models.RotaSlot).filter(
        and_(models.RotaSlot.start < next_month,
             models.RotaSlot.end > first,
             models.RotaSlot.type.in_(["night_call", "day_call"]))
    ).delete(synchronize_session=False)
    db.commit()

    created = 0
    rr_ix = 0  # persistent RR index across days (gives fair spread)
    day = first
    while day < next_month:
        # Eligible contracts (active that day)
        active = (db.query(models.Contract)
                    .join(models.User, models.User.id == models.Contract.user_id)
                    .filter(models.User.role == "nchd")
                    .filter(models.Contract.start <= day.date())
                    .filter((models.Contract.end == None) | (models.Contract.end >= day.date()))
                    .order_by(models.Contract.user_id.asc(), models.Contract.start.asc())
                    .all())

        if active:
            uid_list = [c.user_id for c in active]
            # round-robin pick, but keep user stable if multiple contracts for same person
            chosen_uid = uid_list[rr_ix % len(uid_list)]
            # pick a contract for that user (first match)
            chosen_c = next(c for c in active if c.user_id == chosen_uid)

            start = day.replace(hour=17, minute=0, second=0, microsecond=0)
            end   = (day + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

            slot = models.RotaSlot(
                user_id=chosen_uid,
                post_id=chosen_c.post_id,         # use contract's post
                start=start, end=end,
                type="night_call",
                labels={}
            )
            db.add(slot)
            created += 1
            rr_ix += 1

        day += timedelta(days=1)

    db.commit()
    return schemas.RosterBuildResult(created_slots=created)
    

@api.post("/oncall/update", response_model=schemas.OnCallEvent)
def oncall_update(req: schemas.RosterUpdateRequest, db: Session = Depends(get_db)):
    """
    Minimal updater: reassign a specific on-call slot to another user.
    """
    if not req.slot_id or not req.user_id:
        raise HTTPException(status_code=400, detail="slot_id and user_id are required")
    slot = db.query(models.RotaSlot).get(req.slot_id)
    if not slot or slot.type not in ("night_call","day_call"):
        raise HTTPException(status_code=404, detail="On-call slot not found")
    user = db.query(models.User).get(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    slot.user_id = req.user_id
    db.commit(); db.refresh(slot)
    uname = db.query(models.User.name).filter(models.User.id==slot.user_id).scalar() or "Unassigned"
    return schemas.OnCallEvent(start=slot.start, end=slot.end, type=slot.type, user_id=slot.user_id or 0, user_name=uname)

@api.post("/oncall/assign", response_model=schemas.OnCallEvent)
def oncall_assign(req: schemas.OnCallAssignIn, db: Session = Depends(get_db)):
    post_id = req.post_id
    if not post_id:
        post = db.query(models.Post).first()
        if not post:
            post = models.Post(title="General Service", opd_day="Wed")
            db.add(post); db.commit(); db.refresh(post)
        post_id = post.id
    user = db.query(models.User).get(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    slot = models.RotaSlot(
        user_id=req.user_id, post_id=post_id,
        start=req.start, end=req.end, type=req.type, labels={}
    )
    db.add(slot); db.commit(); db.refresh(slot)
    return schemas.OnCallEvent(
        start=slot.start, end=slot.end, type=slot.type,
        user_id=slot.user_id or 0, user_name=user.name
    )

@api.post("/actions/autofill-by-post")
def autofill_by_post(req: schemas.AutofillByPostIn, db: Session = Depends(get_db)):
    first = datetime(req.year, req.month, 1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    created = 0
    day = first
    while day < next_month:
        # find active contract for this post-day
        c = (db.query(models.Contract)
               .filter(models.Contract.post_id == req.post_id)
               .filter(models.Contract.start <= day.date())
               .filter((models.Contract.end == None) | (models.Contract.end >= day.date()))
               .order_by(models.Contract.start.asc())
               .first())
        if c:
            start = day.replace(hour=17, minute=0)
            end   = (day + timedelta(days=1)).replace(hour=9, minute=0)
            exists = (db.query(models.RotaSlot)
                        .filter(models.RotaSlot.start == start,
                                models.RotaSlot.type == "night_call")
                        .first())
            if not exists:
                db.add(models.RotaSlot(user_id=c.user_id, post_id=req.post_id,
                                       start=start, end=end, type="night_call", labels={}))
                created += 1
        day += timedelta(days=1)
    db.commit()
    return {"status":"ok", "created": created}


from fastapi import Body

# ---- Posts ----
@api.get("/posts", response_model=List[schemas.PostOut])
def list_posts(db: Session = Depends(get_db)):
    return db.query(models.Post).order_by(models.Post.id.asc()).all()

@api.post("/posts", response_model=schemas.PostOut)
def create_post(p: schemas.PostIn, db: Session = Depends(get_db)):
    post = models.Post(title=p.title, opd_day=p.opd_day)
    db.add(post); db.commit(); db.refresh(post)
    return post

@api.patch("/posts/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, patch: schemas.PostIn, db: Session = Depends(get_db)):
    post = db.query(models.Post).get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if patch.title is not None: post.title = patch.title
    if patch.opd_day is not None: post.opd_day = patch.opd_day
    db.commit(); db.refresh(post)
    return post

@api.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post); db.commit()
    return {"status":"deleted","id":post_id}

# ---- Teams ----
@api.get("/teams", response_model=List[schemas.TeamOut])
def list_teams(db: Session = Depends(get_db)):
    return db.query(models.Team).order_by(models.Team.id.asc()).all()

@api.post("/teams", response_model=schemas.TeamOut)
def create_team(t: schemas.TeamIn, db: Session = Depends(get_db)):
    team = models.Team(name=t.name, supervisor_id=t.supervisor_id)
    db.add(team); db.commit(); db.refresh(team)
    return team

@api.patch("/teams/{team_id}", response_model=schemas.TeamOut)
def update_team(team_id: int, patch: schemas.TeamIn, db: Session = Depends(get_db)):
    team = db.query(models.Team).get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if patch.name is not None: team.name = patch.name
    if patch.supervisor_id is not None: team.supervisor_id = patch.supervisor_id
    db.commit(); db.refresh(team)
    return team

@api.delete("/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(models.Team).get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(team); db.commit()
    return {"status":"deleted","id":team_id}

# ---- Contracts ----
@api.get("/contracts", response_model=List[schemas.ContractOut])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).order_by(models.Contract.start.desc()).all()

@api.post("/contracts", response_model=schemas.ContractOut)
def create_contract(c: schemas.ContractIn, db: Session = Depends(get_db)):
    # optional: overlap check (simple)
    overlapping = (
        db.query(models.Contract)
          .filter(models.Contract.user_id == c.user_id)
          .filter(models.Contract.post_id == c.post_id)
          .filter(models.Contract.start <= (c.end or c.start))
          .filter((models.Contract.end == None) | (models.Contract.end >= c.start))
          .first()
    )
    if overlapping:
        raise HTTPException(status_code=400, detail="Overlapping contract exists for this user & post")
    obj = models.Contract(**c.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@api.patch("/contracts/{contract_id}", response_model=schemas.ContractOut)
def update_contract(contract_id: int, patch: schemas.ContractIn, db: Session = Depends(get_db)):
    obj = db.query(models.Contract).get(contract_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Contract not found")
    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj

@api.delete("/contracts/{contract_id}")
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Contract).get(contract_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Contract not found")
    db.delete(obj); db.commit()
    return {"status":"deleted","id":contract_id}

@api.delete("/oncall/{slot_id}")
def oncall_delete(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(models.RotaSlot).get(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="On-call slot not found")
    db.delete(slot); db.commit()
    return {"status": "deleted", "id": slot_id}
