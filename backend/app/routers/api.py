from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models
from ..schemas import PostCreate, PostUpdate, PostOut

router = APIRouter(prefix="/posts", tags=["posts"])

def _post_to_dict(p: models.Post) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "site": p.site,
        "grade": p.grade,
        "fte": p.fte,
        "status": p.status,
        "call_policy": (p.eligibility or {}).get("call_policy", {
            "role": "NCHD", "min_rest_hours": 11, "max_nights_per_month": 7, "participates_in_call": True
        }),
        "notes": p.notes,
    }

@router.get("", response_model=List[Dict[str, Any]])
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return [_post_to_dict(p) for p in posts]

@router.post("")
def create_post(payload: Dict[str, Any], db: Session = Depends(get_db)):
    p = models.Post(
        title=payload.get("title", "Untitled"),
        site=payload.get("site"),
        grade=payload.get("grade"),
        fte=payload.get("fte", 1.0),
        status=payload.get("status", "ACTIVE_ROSTERABLE"),
        core_hours=payload.get("core_hours") or {},
        eligibility=payload.get("eligibility") or {},
        notes=payload.get("notes"),
    )
    db.add(p); db.commit(); db.refresh(p)
    return _post_to_dict(p)

@router.put("/{post_id}")
def update_post(post_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    for k in ["title","site","grade","fte","status","core_hours","eligibility","notes"]:
        if k in payload:
            setattr(p, k, payload[k])
    db.commit(); db.refresh(p)
    return _post_to_dict(p)

@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Post).get(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(p); db.commit()
    return {"ok": True}

router = APIRouter(tags=["core"])

@router.get("/health")
def health():
    return {"ok": True}
# ---- Posts --------------------------------------------------------------------

@router.get("/posts", response_model=List[PostOut])
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).order_by(models.Post.id.asc()).all()
    return posts

@router.post("/posts", response_model=PostOut)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
    post = models.Post(**payload.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.put("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: int, payload: PostUpdate, db: Session = Depends(get_db)):
    post = db.query(models.Post).get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(post, k, v)
    db.commit()
    db.refresh(post)
    return post

@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"ok": True}
