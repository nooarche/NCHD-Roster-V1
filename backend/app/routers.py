
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
