from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from .db import get_db
from . import models

api = APIRouter()

# ---------- helpers ----------
def _as_json(obj: Any) -> Dict[str, Any]:
    """Return a dict for JSON-like fields; tolerate None/str/other."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    # In case old rows still store text
    try:
        import json
        return json.loads(obj) if isinstance(obj, str) else {}
    except Exception:
        return {}

def _user_to_dict(u: models.User) -> Dict[str, Any]:
    return {
        "id": u.id, "name": u.name, "email": u.email,
        "role": u.role, "grade": u.grade, "site": u.site, "active": u.active
    }

def _group_to_dict(g: models.Group) -> Dict[str, Any]:
    return {"id": g.id, "name": g.name, "kind": g.kind, "rules": _as_json(g.rules)}

def _post_to_dict(p: models.Post) -> Dict[str, Any]:
    core = _as_json(getattr(p, "core_hours", {}))
    elig = _as_json(getattr(p, "eligibility", {}))
    call_policy = _as_json(elig.get("call_policy")) or {
        "participates_in_call": True,
        "max_nights_per_month": 7,
        "min_rest_hours": 11,
        "role": "NCHD",
    }
    return {
        "id": p.id, "title": p.title, "site": p.site, "grade": p.grade,
        "fte": float(p.fte or 1.0), "status": p.status,
        "core_hours": core, "eligibility": elig, "notes": p.notes,
        "group_ids": [g.id for g in p.groups],
        "call_policy": call_policy,
    }

# ---------- health ----------
@api.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}

# ---------- users ----------
@api.get("/users")
def list_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return [_user_to_dict(u) for u in users]

# ---------- groups (CRUD) ----------
@api.get("/groups")
def list_groups(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    gs = db.query(models.Group).order_by(models.Group.id.asc()).all()
    return [_group_to_dict(g) for g in gs]

@api.post("/groups")
def create_group(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    if "name" not in data or "kind" not in data:
        raise HTTPException(400, "name and kind are required")
    g = models.Group(name=data["name"], kind=data["kind"], rules=data.get("rules") or {})
    db.add(g); db.commit(); db.refresh(g)
    return _group_to_dict(g)

@api.put("/groups/{group_id}")
def update_group(group_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    g = db.query(models.Group).get(group_id)
    if not g: raise HTTPException(404, "Group not found")
    if "name" in data: g.name = data["name"]
    if "kind" in data: g.kind = data["kind"]
    if "rules" in data: g.rules = data["rules"] or {}
    db.commit(); db.refresh(g)
    return _group_to_dict(g)

@api.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    g = db.query(models.Group).get(group_id)
    if not g: raise HTTPException(404, "Group not found")
    db.delete(g); db.commit()
    return {"status": "ok", "deleted": group_id}

# ---------- posts (CRUD) ----------
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
        core_hours=data.get("core_hours") or {},
        eligibility=data.get("eligibility") or {},
        notes=data.get("notes"),
    )
    if "call_policy" in data:
        elig = _as_json(p.eligibility)
        elig["call_policy"] = data["call_policy"] or {}
        p.eligibility = elig

    group_ids = data.get("group_ids") or []
    if group_ids:
        groups = db.query(models.Group).filter(models.Group.id.in_(group_ids)).all()
        p.groups = groups

    db.add(p); db.commit(); db.refresh(p)
    return _post_to_dict(p)

@api.put("/posts/{post_id}")
def update_post(post_id: int, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p: raise HTTPException(404, "Post not found")

    for k in ["title","site","grade","fte","status","notes"]:
        if k in data: setattr(p, k, data[k])
    if "core_hours" in data: p.core_hours = data["core_hours"] or {}
    if "eligibility" in data: p.eligibility = data["eligibility"] or {}
    if "call_policy" in data:
        elig = _as_json(p.eligibility)
        elig["call_policy"] = data["call_policy"] or {}
        p.eligibility = elig

    if "group_ids" in data:
        gids = data["group_ids"] or []
        groups = db.query(models.Group).filter(models.Group.id.in_(gids)).all() if gids else []
        p.groups = groups

    db.commit(); db.refresh(p)
    return _post_to_dict(p)

@api.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = db.query(models.Post).get(post_id)
    if not p: raise HTTPException(404, "Post not found")
    db.delete(p); db.commit()
    return {"status": "ok", "deleted": post_id}
