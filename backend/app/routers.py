# backend/app/routers.py — REPLACE ENTIRE FILE

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

from .db import get_db
from . import models

api = APIRouter()

# ---------- SMALL HELPERS ----------

def _post_to_dict(p: models.Post) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "site": getattr(p, "site", None),
        "grade": getattr(p, "grade", None),
        "fte": getattr(p, "fte", 1.0),
        "status": getattr(p, "status", "ACTIVE_ROSTERABLE"),
        "opd": getattr(p, "opd", None),
        "teaching": getattr(p, "teaching", None),
        "supervision": getattr(p, "supervision", None),
        "core_hours": getattr(p, "core_hours", None),
        "eligibility": getattr(p, "eligibility", None),
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

# ---------- HEALTH ----------

@api.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}

# ---------- USERS ----------

@api.get("/users")
def list_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return [_user_to_dict(u) for u in users]

@api.post("/users")
def create_user(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    u = models.User(
        name=data.get("name", "Unnamed"),
        email=data.get("email"),
        role=data.get("role", "nchd"),
        grade=data.get("grade"),
        site=data.get("site"),
        active=data.get("active", True),
    )
    db.add(u); db.commit(); db.refresh(u)
    return _user_to_dict(u)

# ---------- POSTS ----------

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
        opd=data.get("opd"),
        teaching=data.get("teaching"),
        supervision=data.get("supervision"),
        core_hours=data.get("core_hours"),
        eligibility=data.get("eligibility"),
        notes=data.get("notes"),
    )
    db.add(p); db.commit(); db.refresh(p)
    return _post_to_dict(p)

@api.put("/posts/{post_id}")
def update_post(post_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    for k, v in data.items():
        if hasattr(p, k):
            setattr(p, k, v)
    db.commit(); db.refresh(p)
    return _post_to_dict(p)

@api.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    db.delete(p); db.commit()
    return {"status": "ok", "deleted": post_id}

# ---------- VACANCY WINDOWS ----------

@api.get("/posts/{post_id}/vacancy")
def list_vacancy(post_id: int, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    wins = db.query(models.VacancyWindow).filter_by(post_id=post_id).order_by(models.VacancyWindow.start_date.asc()).all()
    out = []
    for w in wins:
        out.append({
            "id": w.id,
            "post_id": w.post_id,
            "status": w.status,
            "start_date": w.start_date.isoformat(),
            "end_date": w.end_date.isoformat() if w.end_date else None
        })
    return out

@api.post("/posts/{post_id}/vacancy")
def add_vacancy(post_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(404, "Post not found")
    w = models.VacancyWindow(
        post_id=post_id,
        status=data.get("status", "VACANT_UNROSTERABLE"),
        start_date=date.fromisoformat(data["start_date"]),
        end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None
    )
    db.add(w); db.commit(); db.refresh(w)
    return {
        "id": w.id,
        "post_id": w.post_id,
        "status": w.status,
        "start_date": w.start_date.isoformat(),
        "end_date": w.end_date.isoformat() if w.end_date else None
    }

# ---------- AUTOFILL (NIGHT CALL) ----------

def _is_post_unrosterable_today(p: models.Post, today: date) -> bool:
    if getattr(p, "status", "ACTIVE_ROSTERABLE") == "VACANT_UNROSTERABLE":
        return True
    for w in getattr(p, "vacancy_windows", []) or []:
        if w.status == "VACANT_UNROSTERABLE" and w.start_date <= today and (w.end_date is None or w.end_date >= today):
            return True
    return False

def _eligible_users(db: Session):
    q = db.query(models.User).filter(models.User.active == True)
    return [u for u in q.all() if (getattr(u, "role", "nchd") or "").lower() == "nchd"]

def _has_rest_conflict(db: Session, user_id: int, new_start: datetime, new_end: datetime, min_rest_hours: int = 11) -> bool:
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

@api.post("/oncall/autofill")
def oncall_autofill(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Payload example:
    { "year": 2025, "month": 10, "night_calls_per_day": 1 }
    """
    year = int(payload["year"]); month = int(payload["month"])
    night_calls_per_day = int(payload.get("night_calls_per_day", 1))

    first = datetime(year, month, 1)
    nm = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    posts = [p for p in db.query(models.Post).all() if not _is_post_unrosterable_today(p, date.today())]
    users = _eligible_users(db)
    if not users:
        return {"created_slots": 0, "message": "No eligible NCHD users"}

    created = 0
    idx = 0
    d = first
    while d < nm:
        if night_calls_per_day > 0:
            start = d.replace(hour=17, minute=0, second=0, microsecond=0)
            end = (d + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

            chosen = None
            for _ in range(len(users)):
                u = users[idx % len(users)]
                idx += 1
                if not _has_rest_conflict(db, u.id, start, end, 11):
                    chosen = u
                    break

            if chosen:
                slot = models.RotaSlot(
                    user_id=chosen.id,
                    post_id=posts[0].id if posts else None,
                    start=start,
                    end=end,
                    type="night_call",
                    labels={}
                )
                db.add(slot); created += 1
        d += timedelta(days=1)

    db.commit()
    return {"created_slots": created}
