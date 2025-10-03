# backend/app/routers/groups.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from ..db import get_db
from .. import models

router = APIRouter(prefix="/groups", tags=["groups"])

# --- simple Pydantic-free payload typing (dict passthrough) ---
def _to_dict(g: models.Group) -> Dict[str, Any]:
    return {
        "id": g.id,
        "name": g.name,
        "kind": g.kind,
        "rules": g.rules or {},
        "notes": g.notes,
    }

@router.get("", response_model=List[Dict[str, Any]])  # GET /groups
def list_groups(db: Session = Depends(get_db)):
    groups = db.query(models.Group).order_by(models.Group.id).all()
    return [_to_dict(g) for g in groups]

@router.post("", response_model=Dict[str, Any])       # POST /groups
def create_group(payload: Dict[str, Any], db: Session = Depends(get_db)):
    name = payload.get("name")
    kind = payload.get("kind")
    if not name or not kind:
        raise HTTPException(status_code=400, detail="name and kind are required")

    g = models.Group(
        name=name,
        kind=kind,
        rules=payload.get("rules") or {},
        notes=payload.get("notes"),
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return _to_dict(g)

@router.put("/{group_id}", response_model=Dict[str, Any])  # PUT /groups/{id}
def update_group(group_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    g = db.query(models.Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")

    if "name" in payload: g.name = payload["name"]
    if "kind" in payload: g.kind = payload["kind"]
    if "rules" in payload: g.rules = payload["rules"] or {}
    if "notes" in payload: g.notes = payload["notes"]
    db.commit()
    db.refresh(g)
    return _to_dict(g)

@router.delete("/{group_id}", response_model=Dict[str, Any])  # DELETE /groups/{id}
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(models.Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(g)
    db.commit()
    return {"ok": True, "id": group_id}
