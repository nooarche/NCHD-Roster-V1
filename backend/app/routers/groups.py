from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Group, Post, PostGroup

router = APIRouter(prefix="/groups", tags=["groups"])

# ---------- Schemas ----------
class GroupIn(BaseModel):
    name: str
    kind: str  # e.g. "on_call_pool" | "protected_teaching" | "clinic_team"
    rules: Dict[str, Any] = Field(default_factory=dict)

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None

class GroupOut(BaseModel):
    id: int
    name: str
    kind: str
    rules: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True  # Pydantic v2: reads from SQLAlchemy model attrs


def _group_to_out(g: Group) -> GroupOut:
    # Defensive defaults in case rules is None
    return GroupOut(
        id=g.id,
        name=g.name,
        kind=g.kind,
        rules=g.rules or {},
    )

# ---------- CRUD ----------
@router.get("", response_model=list[GroupOut])
def list_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).order_by(Group.id.asc()).all()
    return [_group_to_out(g) for g in groups]

@router.post("", response_model=GroupOut)
def create_group(payload: GroupIn, db: Session = Depends(get_db)):
    g = Group(name=payload.name, kind=payload.kind, rules=payload.rules or {})
    db.add(g)
    db.commit()
    db.refresh(g)
    return _group_to_out(g)

@router.get("/{group_id}", response_model=GroupOut)
def get_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    return _group_to_out(g)

@router.put("/{group_id}", response_model=GroupOut)
def update_group(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")

    if payload.name is not None:
        g.name = payload.name
    if payload.kind is not None:
        g.kind = payload.kind
    if payload.rules is not None:
        g.rules = payload.rules

    db.commit()
    db.refresh(g)
    return _group_to_out(g)

@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(g)
    db.commit()
    return {"ok": True}

# ---------- Post <-> Group association helpers ----------
@router.post("/{group_id}/posts/{post_id}")
def add_post_to_group(group_id: int, post_id: int, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    p = db.query(Post).get(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    # check existing link
    exists = (
        db.query(PostGroup)
        .filter(PostGroup.group_id == group_id, PostGroup.post_id == post_id)
        .first()
    )
    if not exists:
        db.add(PostGroup(group_id=group_id, post_id=post_id))
        db.commit()
    return {"ok": True}

@router.delete("/{group_id}/posts/{post_id}")
def remove_post_from_group(group_id: int, post_id: int, db: Session = Depends(get_db)):
    link = (
        db.query(PostGroup)
        .filter(PostGroup.group_id == group_id, PostGroup.post_id == post_id)
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    return {"ok": True}
