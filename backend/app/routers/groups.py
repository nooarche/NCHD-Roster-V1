from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any
from ..db import get_db
from .. import models
from ..schemas.group import GroupCreate, GroupRead, GroupUpdate

router = APIRouter(prefix="/groups", tags=["groups"])

def _has_group_model() -> bool:
    return hasattr(models, "Group") and hasattr(models, "Activity")

@router.get("", response_model=list[GroupRead])
def list_groups(db: Session = Depends(get_db)):
    if not _has_group_model():
        return []  # stub mode: empty list
    return db.query(models.Group).all()

@router.post("", response_model=GroupRead)
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    if not _has_group_model():
        raise HTTPException(501, "Groups persistence not enabled (missing Group/Activity models). See README-DROPIN.md.")
    g = models.Group(
        name=payload.name,
        kind=payload.kind,
        rules=payload.rules or {},
    )
    db.add(g); db.flush()
    if payload.activities:
        for a in payload.activities:
            g.activities.append(models.Activity(**a.model_dump()))
    db.commit(); db.refresh(g)
    return g

@router.put("/{group_id}", response_model=GroupRead)
def update_group(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db)):
    if not _has_group_model():
        raise HTTPException(501, "Groups persistence not enabled (missing Group/Activity models). See README-DROPIN.md.")
    g = db.get(models.Group, group_id)
    if not g:
        raise HTTPException(404, "Group not found")
    if payload.name is not None: g.name = payload.name
    if payload.kind is not None: g.kind = payload.kind
    if payload.rules is not None: g.rules = payload.rules
    if payload.activities is not None:
        g.activities.clear()
        for a in payload.activities:
            g.activities.append(models.Activity(**a.model_dump()))
    db.commit(); db.refresh(g)
    return g

@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    if not _has_group_model():
        raise HTTPException(501, "Groups persistence not enabled (missing Group/Activity models). See README-DROPIN.md.")
    g = db.get(models.Group, group_id)
    if not g:
        raise HTTPException(404, "Group not found")
    db.delete(g); db.commit()
    return {"ok": True}
