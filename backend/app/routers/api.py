# backend/app/routers/api.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List
import json

from ..db import get_db
from .. import models

router = APIRouter(tags=["core"])

# --- helpers -------------------------------------------------------------------
def _as_json(obj) -> Dict[str, Any]:
    """
    Safely coerce DB values that might be dict/JSONB, None, or a JSON string.
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            val = json.loads(obj)
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}
    return {}

def _post_to_dict(p: models.Post) -> Dict[str, Any]:
    eligibility = _as_json(p.eligibility)
    call_policy = eligibility.get(
        "call_policy",
        {
            "role": "NCHD",
            "min_rest_hours": 11,
            "max_nights_per_month": 7,
            "participates_in_call": True,
        },
    )
    return {
        "id": p.id,
        "title": p.title,
        "site": p.site,
        "grade": p.grade,
        "fte": p.fte,
        "status": p.status,
        "call_policy": call_policy,
        "notes": p.notes,
    }

# --- health --------------------------------------------------------------------
@router.get("/health")
def health():
    return {"ok": True}

# --- posts ---------------------------------------------------------------------
@router.get("/posts", response_model=List[Dict[str, Any]])
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).order_by(models.Post.id.asc()).all()
    return [_post_to_dict(p) for p in posts]

@router.post("/posts")
def create_post(payload: Dict[str, Any], db: Session = Depends(get_db)):
    p = models.Post(
        title=payload.get("title", "Untitled"),
        site=payload.get("site"),
        grade=payload.get("grade"),
        fte=payload.get("fte", 1.0),
        status=payload.get("status", "ACTIVE_ROSTERABLE"),
        core_hours=_as_json(payload.get("core_hours")),
        eligibility=_as_json(payload.get("eligibility")),
        notes=payload.get("notes"),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _post_to_dict(p)

@router.put("/posts/{post_id}")
def update_post(post_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    # coerce possibly-string JSON fields
    updates = dict(payload)
    if "core_hours" in updates:
        updates["core_hours"] = _as_json(updates["core_hours"])
    if "eligibility" in updates:
        updates["eligibility"] = _as_json(updates["eligibility"])

    for k in ["title", "site", "grade", "fte", "status", "core_hours", "eligibility", "notes"]:
        if k in updates:
            setattr(p, k, updates[k])

    db.commit()
    db.refresh(p)
    return _post_to_dict(p)

@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(p)
    db.commit()
    return {"ok": True}
