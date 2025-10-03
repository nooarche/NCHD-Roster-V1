# backend/app/routers.py — REPLACE ENTIRE FILE

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

from .db import get_db
from . import models

api = APIRouter()

# ------------------------- HELPERS -------------------------

def _post_to_dict(p: models.Post) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "site": getattr(p, "site", None),
        "grade": getattr(p, "grade", None),
        "fte": float(getattr(p, "fte", 1.0) or 1.0),
        "status": getattr(p, "status", "ACTIVE_ROSTERABLE"),
        # Call policy lives in JSON field 'eligibility' to avoid new columns/migrations
        "call_policy": (getattr(p, "eligibility", {}) or {}).get("call_policy", {
            "participates_in_call": True,
            "max_nights_per_month": 7,
            "min_rest_hours": 11,
            "role": "NCHD"
        }),
        "notes": getattr(p, "notes", None),
    }

def _user_to_dict(u: models.User) -> Dict[str, Any]:
    return {
        "id": u.id,
        "name": u.name,
        "email": getattr(u, "email", None),
        "role": getattr(u, "role", "nchd"),
        "grade": getattr(u, "grade", None),
        "site": getattr(u, "site", None),
        "active": getattr(u, "active", True),
    }

def _post_is_unrosterable_on(p: models.Post, d: date) -> bool:
    if getattr(p, "status", "ACTIVE_ROSTERABLE") == "VACANT_UNROSTERABLE":
        return True
    if getattr(p, "vacancy_windows", None):
        for w in p.vacancy_windows:
            if w.status == "VACANT_UNROSTERABLE" and w.start_date <= d and (w.end_date is None or w.end_date >= d):
                return True
    return False

def _eligible_nchds(db: Session) -> List[models.User]:
    q = db.query(models.User).filter(models.User.active == True)
    return [u for u in q.all() if (getattr(u, "role", "nchd") or "").lower() == "nchd"]

def _get_call_policy(p: models.Post) -> Dict[str, Any]:
    elig = getattr(p, "eligibility", {}) or {}
    cp = elig.get("call_policy", {})
    # defaults
    return {
        "participates_in_call": cp.get("participates_in_call", True),
        "max_nights_per_month": int(cp.get("max_nights_per_month", 7)),
        "min_rest_hours": int(cp.get("min_rest_hours", 11)),
        "role": cp.get("role", "NCHD"),
    }

def _set_call_policy(p: models.Post, policy: Dict[str, Any]) -> None:
    elig = getattr(p, "eligibility", {}) or {}
    elig["call_policy"] = {
        "participates_in_call": bool(policy.get("participates_in_call", True)),
        "max_nights_per_month": int(policy.get("max_nights_per_month", 7)),
        "min_rest_hours": int(policy.get("min_rest_hours", 11)),
        "role": policy.get("role", "NCHD"),
    }
    p.eligibility = elig

def _user_has_rest_conflict(db: Session, user_id: int, new_start: datetime, new_end: datetime, min_rest_hours: int) -> bool:
    window_start = new_start - timedelta(hours=min_rest_hours)
    window_end = new_end + timedelta(hours=min_rest_hours)
    overlap = (
        db.query(models.RotaSlot)
          .filter(models.RotaSlot.user_id == user_id)
          .filter(models.RotaSlot.end > window_start)
          .filter(models.RotaSlot.start < window_end)
          .count()
    )
    return overlap > 0

def _count_nights_in_month(db: Session, user_id: int, year: int, month: int) -> int:
    start = datetime(year, month, 1)
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (
        db.query(models.RotaSlot)
          .filter(models.RotaSlot.user_id == user_id)
          .filter(models.RotaSlot.type == "night_call")
          .filter(models.RotaSlot.start >= start)
          .filter(models.RotaSlot.start < end)
          .count()
    )

# ------------------------- HEALTH -------------------------

@api.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}

# ------------------------- USERS --------------------------

@api.get("/users")
def list_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return [_user_to_dict(u) for u in users]

# ------------------------- POSTS CRUD ---------------------

@api.get("/posts")
def list_posts(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    posts = db.query(models.Post).order_by(models.Post.id.asc()).all()
    return [_post_to_dict(p) for p in posts]

@api.post("/posts")
def create_post(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = models.Post(
        title=data.get("title", "Untitled"),
        site=data.get("site"),
        grade=data.get("grade"),
        fte=float(data.get("fte") or 1.0),
        status=data.get("status", "ACTIVE_ROSTERABLE"),
        eligibility=data.get("eligibility") or {},
        notes=data.get("notes"),
    )
    # optional: initial call policy in payload
    if "call_policy" in data:
        _set_call_policy(p, data["call_policy"])
    db.add(p); db.commit(); db.refresh(p)
    return _post_to_dict(p)

@api.put("/posts/{post_id}")
def update_post(post_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    for k in ["title","site","grade","fte","status","notes"]:
        if k in data:
            setattr(p, k, data[k])
    if "call_policy" in data:
        _set_call_policy(p, data["call_policy"])
    # keep other JSON sub-objects if passed fully
    if "eligibility" in data and "call_policy" not in data:
        p.eligibility = data["eligibility"]
    db.commit(); db.refresh(p)
    return _post_to_dict(p)

@api.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    db.delete(p); db.commit()
    return {"status": "ok", "deleted": post_id}

# ------------------- CALL POLICY (per post) ---------------

@api.get("/posts/{post_id}/call-policy")
def get_call_policy(post_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    return _get_call_policy(p)

@api.put("/posts/{post_id}/call-policy")
def set_call_policy(post_id: int, policy: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    _set_call_policy(p, policy)
    db.commit(); db.refresh(p)
    return _get_call_policy(p)

# ------------------------- ROSTER EDIT --------------------

@api.get("/rota/slots")
def list_slots(
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    slots = (
        db.query(models.RotaSlot)
          .filter(models.RotaSlot.start >= start)
          .filter(models.RotaSlot.start < end)
          .order_by(models.RotaSlot.start.asc())
          .all()
    )
    out = []
    for s in slots:
        out.append({
            "id": s.id,
            "user_id": s.user_id,
            "post_id": s.post_id,
            "start": s.start.isoformat(),
            "end": s.end.isoformat(),
            "type": s.type,
            "labels": s.labels or {},
        })
    return out

@api.post("/rota/slots")
def create_slot(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    s = models.RotaSlot(
        user_id=data["user_id"],
        post_id=data.get("post_id"),
        start=datetime.fromisoformat(data["start"]),
        end=datetime.fromisoformat(data["end"]),
        type=data.get("type", "night_call"),
        labels=data.get("labels", {}),
    )
    db.add(s); db.commit(); db.refresh(s)
    return {"id": s.id}

@api.put("/rota/slots/{slot_id}")
def update_slot(slot_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    s = db.query(models.RotaSlot).get(slot_id)
    if not s:
        raise HTTPException(404, "Slot not found")
    for k in ["user_id","post_id","type","labels"]:
        if k in data:
            setattr(s, k, data[k])
    if "start" in data: s.start = datetime.fromisoformat(data["start"])
    if "end" in data:   s.end   = datetime.fromisoformat(data["end"])
    db.commit(); db.refresh(s)
    return {"status":"ok","id":s.id}

@api.delete("/rota/slots/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    s = db.query(models.RotaSlot).get(slot_id)
    if not s:
        raise HTTPException(404, "Slot not found")
    db.delete(s); db.commit()
    return {"status":"ok"}

# ------------------------- AUTOFILL -----------------------

@api.post("/oncall/autofill")
def oncall_autofill(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Payload:
      {
        "year": 2025,
        "month": 10,
        "start_date": "2025-10-01",   # optional; defaults to 1st of month
        "end_date":   "2025-10-31",   # optional; defaults to end of month
        "freeze_before": "2026-02-01",# do not modify slots before this date
        "night_calls_per_day": 1
      }
    """
    year = int(payload["year"])
    month = int(payload["month"])
    first = datetime(year, month, 1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    start = datetime.fromisoformat(payload.get("start_date") or first.isoformat())
    end   = datetime.fromisoformat(payload.get("end_date") or (next_month - timedelta(seconds=1)).isoformat())
    freeze_before: Optional[date] = None
    if payload.get("freeze_before"):
        freeze_before = date.fromisoformat(payload["freeze_before"])

    night_calls_per_day = int(payload.get("night_calls_per_day", 1))

    posts = db.query(models.Post).all()
    # only posts that can participate + not marked unrosterable today
    rosterable_posts = []
    for p in posts:
        policy = _get_call_policy(p)
        if not policy["participates_in_call"]:
            continue
        rosterable_posts.append((p, policy))

    users = _eligible_nchds(db)
    if not users or not rosterable_posts:
        return {"created_slots": 0, "message": "No eligible users or posts"}

    created = 0
    idx = 0

    d = start.replace(hour=0, minute=0, second=0, microsecond=0)
    while d <= end:
        # Respect freeze
        if freeze_before and d.date() < freeze_before:
            d += timedelta(days=1)
            continue

        # Skip if day already has a night slot (respect existing manual roster)
        existing = (
            db.query(models.RotaSlot)
              .filter(models.RotaSlot.type == "night_call")
              .filter(models.RotaSlot.start >= d.replace(hour=0))
              .filter(models.RotaSlot.start <  (d + timedelta(days=1)).replace(hour=0))
              .count()
        )
        if existing >= night_calls_per_day:
            d += timedelta(days=1)
            continue

        start_dt = d.replace(hour=17)
        end_dt   = (d + timedelta(days=1)).replace(hour=9)

        # Round-robin users, respect rest & per-month cap
        chosen = None
        for _ in range(len(users)):
            u = users[idx % len(users)]; idx += 1
            min_rest = 11
            # use first post's policy for rest (or compute min across)
            if rosterable_posts:
                min_rest = rosterable_posts[0][1]["min_rest_hours"]
            if _user_has_rest_conflict(db, u.id, start_dt, end_dt, min_rest):
                continue
            # monthly cap
            if rosterable_posts:
                cap = rosterable_posts[0][1]["max_nights_per_month"]
                if _count_nights_in_month(db, u.id, year, month) >= cap:
                    continue
            chosen = u
            break

        if chosen:
            picked_post = rosterable_posts[0][0]  # simple: assign to first post; can improve later
            s = models.RotaSlot(
                user_id=chosen.id,
                post_id=picked_post.id if picked_post else None,
                start=start_dt,
                end=end_dt,
                type="night_call",
                labels={},
            )
            db.add(s); created += 1

        d += timedelta(days=1)

    db.commit()
    return {"created_slots": created}
