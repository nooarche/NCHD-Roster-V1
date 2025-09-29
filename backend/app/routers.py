
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from . import models, schemas
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import and_

api = APIRouter()

@api.get("/health")
def health():
    return {"status": "ok"}

@api.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

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
    from sqlalchemy import func
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
            start=slot.start, end=slot.end, type=slot.type,
            user_id=slot.user_id or 0, user_name=uname or "Unassigned"
        ))
    return out

@api.get("/validate/rota", response_model=schemas.ValidationReport)
def validate_rota(db: Session = Depends(get_db)):
    """
    Minimal checks (extend as needed):
      - Duty length <= 24h (EWTD)
      - Each calendar day has at most one night_call (simple duplication guard)
    """
    issues: list[schemas.ValidationIssue] = []

    # 24h duty check
    slots = (
        db.query(models.RotaSlot, models.User.name)
          .join(models.User, models.User.id == models.RotaSlot.user_id, isouter=True)
          .all()
    )
    for slot, uname in slots:
        hours = (slot.end - slot.start).total_seconds() / 3600.0
        if hours > 24.0:
            issues.append(schemas.ValidationIssue(
                user_id=slot.user_id or 0,
                user_name=uname or "Unassigned",
                slot_id=slot.id,
                message=f"Duty exceeds 24h ({hours:.1f}h)"
            ))

    # one night_call per day (simple)
    from collections import defaultdict
    per_day = defaultdict(list)
    for slot, _ in slots:
        if slot.type == "night_call":
            key = slot.start.date()
            per_day[key].append(slot.id)
    for day, ids in per_day.items():
        if len(ids) > 1:
            for sid in ids[1:]:
                issues.append(schemas.ValidationIssue(
                    user_id=0, user_name="—", slot_id=sid,
                    message=f"Multiple night_call assignments on {day}"
                ))

    return schemas.ValidationReport(ok=(len(issues) == 0), issues=issues)

@api.post("/actions/roster-build", response_model=schemas.RosterBuildResult)
def roster_build(req: schemas.RosterBuildRequest, db: Session = Depends(get_db)):
    """
    Build a month of on-call:
      - Ensures at least one Post exists (creates 'General Service' if none)
      - Clears existing on-call in [month_start, next_month)
      - Assigns 1 night_call per day round-robin across eligible users
    """
    first = datetime(req.year, req.month, 1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    # Ensure a Post exists (to satisfy NOT NULL post_id schemas)
    post = db.query(models.Post).first()
    if not post:
        post = models.Post(title="General Service", opd_day="Wed")
        db.add(post)
        db.commit(); db.refresh(post)

    # Eligible users
    pool = (
        db.query(models.User)
          .filter(models.User.role.in_(req.pool_roles))
          .order_by(models.User.id.asc())
          .all()
    )
    if not pool:
        raise HTTPException(status_code=400, detail="No eligible users found for pool_roles")
    pool_ids = [u.id for u in pool]

    # Wipe existing on-call in window
    db.query(models.RotaSlot).filter(
        and_(models.RotaSlot.start < next_month,
             models.RotaSlot.end > first,
             models.RotaSlot.type.in_(["night_call","day_call"]))
    ).delete(synchronize_session=False)
    db.commit()

    # Assign night calls
    created = 0
    idx = 0
    day = first
    while day < next_month:
        start = day.replace(hour=17, minute=0, second=0, microsecond=0)
        end   = (day + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        uid = pool_ids[idx % len(pool_ids)]
        slot = models.RotaSlot(
            user_id=uid,
            post_id=post.id,             # ← ensure NOT NULL
            start=start, end=end,
            type="night_call",
            labels={}
        )
        db.add(slot)
        created += 1
        idx += 1
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
