
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
@api.post("/actions/roster-build")
def roster_build(db: Session = Depends(get_db)):
    # TODO: load constraints, generate slots, apply OPD guards, run EWTD/fairness validators
    return {"status": "queued", "summary": "Roster build stubbed. Seed data provides initial roster."}

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
    # window [first_day, first_day_next)
    first = datetime(year, month, 1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    q = (
        db.query(models.RotaSlot, models.User.name)
          .join(models.User, models.User.id == models.RotaSlot.user_id)
          .filter(
              and_(models.RotaSlot.start < next_month,
                   models.RotaSlot.end > first,
                   models.RotaSlot.type.in_(["night_call", "day_call"]))
          )
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
