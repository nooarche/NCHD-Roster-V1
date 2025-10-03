from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models
from ..schemas.group import GroupCreate, GroupOut, ActivityCreate, ActivityOut

router = APIRouter(prefix="/groups", tags=["groups"])

@router.get("", response_model=List[GroupOut])
def list_groups(db: Session = Depends(get_db)):
    groups = db.query(models.Group).all()
    out: List[GroupOut] = []
    for g in groups:
        out.append(GroupOut(
            id=g.id, name=g.name, kind=g.kind, rules=g.rules or {},
            activities=[ActivityOut(id=a.id, group_id=g.id, name=a.name, kind=a.kind, pattern=a.pattern or {}) for a in (g.activities or [])]
        ))
    return out

@router.post("", response_model=GroupOut)
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    g = models.Group(name=payload.name, kind=payload.kind, rules=payload.rules or {})
    db.add(g); db.commit(); db.refresh(g)
    return GroupOut(id=g.id, name=g.name, kind=g.kind, rules=g.rules, activities=[])

@router.put("/{group_id}", response_model=GroupOut)
def update_group(group_id: int, payload: GroupCreate, db: Session = Depends(get_db)):
    g = db.query(models.Group).get(group_id)
    if not g:
        raise HTTPException(404, "Group not found")
    g.name = payload.name
    g.kind = payload.kind
    g.rules = payload.rules or {}
    db.commit(); db.refresh(g)
    acts = [ActivityOut(id=a.id, group_id=g.id, name=a.name, kind=a.kind, pattern=a.pattern or {}) for a in g.activities or []]
    return GroupOut(id=g.id, name=g.name, kind=g.kind, rules=g.rules, activities=acts)

@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(models.Group).get(group_id)
    if not g:
        raise HTTPException(404, "Group not found")
    db.delete(g); db.commit()
    return {"ok": True}

@router.post("/{group_id}/activities", response_model=ActivityOut)
def add_activity(group_id: int, payload: ActivityCreate, db: Session = Depends(get_db)):
    g = db.query(models.Group).get(group_id)
    if not g:
        raise HTTPException(404, "Group not found")
    a = models.Activity(group_id=group_id, name=payload.name, kind=payload.kind, pattern=payload.pattern or {})
    db.add(a); db.commit(); db.refresh(a)
    return ActivityOut(id=a.id, group_id=group_id, name=a.name, kind=a.kind, pattern=a.pattern or {})

@router.delete("/{group_id}/activities/{activity_id}")
def remove_activity(group_id: int, activity_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Activity).get(activity_id)
    if not a or a.group_id != group_id:
        raise HTTPException(404, "Activity not found")
    db.delete(a); db.commit()
    return {"ok": True}
