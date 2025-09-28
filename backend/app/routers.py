
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from . import models, schemas
from typing import List

api = APIRouter()

@api.get("/health")
def health():
    return {"status": "ok"}

@api.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@api.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    u = models.User(name=user.name, email=user.email, role=user.role)
    db.add(u); db.commit(); db.refresh(u)
    return u

# Example action endpoints (roster build, refresh) — stubs
@api.post("/actions/roster-build")
def roster_build(db: Session = Depends(get_db)):
    # TODO: load constraints, generate slots, apply OPD guards, run EWTD/fairness validators
    return {"status": "queued", "summary": "Roster build stubbed. Seed data provides initial roster."}

@api.post("/actions/roster-refresh")
def roster_refresh(db: Session = Depends(get_db)):
    return {"status": "ok", "message": "Roster refresh stubbed."}

@api.patch("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, patch: schemas.UserUpdate, db: Session = Depends(get_db)):
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if patch.name is not None: u.name = patch.name
    if patch.email is not None: u.email = patch.email
    if patch.role is not None: u.role = patch.role
    db.commit(); db.refresh(u)
    return u

@api.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u); db.commit()
    return {"status": "deleted", "id": user_id}
