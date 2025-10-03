# backend/app/routers/groups.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from ..db import get_db
from .. import models

router = APIRouter(prefix="/groups", tags=["groups"])

def _group_to_dict(g: models.Group) -> Dict[str, Any]:
    return {
        "id": g.id,
        "name": g.name,
        "kind": g.kind,
        "rules": g.rules or {},
    }

@router.get("", response_model=List[Dict[str, Any]])
def list_groups(db: Session = Depends(get_db)):
    groups = db.query(models.Group).all()
    return [_group_to_dict(g) for g in groups]

@router.post("", response_model=Dict[str, Any])
def create_group(payload: Dict[str, Any], db: Session = Depends(get_db)):
    g = models.Group(
        name=payload.get("name", "Untitled Group"),
        kind=payload.get("kind", "generic"),
        rules=payload.get("rules") or {},
    )
    db.add(g); db.commit(); db.refresh(g)
    return _group_to_dict(g)

@router.put("/{group_id}", response_model=Dict[str, Any])
def update_group(group_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    g = db.query(models.Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    for k in ["name", "kind", "rules"]:
        if k in payload:
            setattr(g, k, payload[k])
    db.commit(); db.refresh(g)
    return _group_to_dict(g)

@router.delete("/{group_id}", response_model=Dict[str, bool])
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(models.Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(g); db.commit()
    return {"ok": True}
