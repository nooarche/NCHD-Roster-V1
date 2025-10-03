from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import api
from .db import engine, Base, SessionLocal
from .seed import seed
from . import models  # ensure models are imported so metadata knows all tables

import time
from sqlalchemy.exc import OperationalError
from .routers import groups, solve  # NEW

app.include_router(groups.router)   # NEW
app.include_router(solve.router)    # NEW
app = FastAPI(title="NCHD Rostering & Leave System API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",          # <— add this
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api)
from .routers import groups  # ANCHOR: GROUPS_ROUTER_IMPORT
app.include_router(groups.router)

@app.on_event("startup")
def on_startup():
    # retry for DB readiness (max ~30s)
    for attempt in range(30):
        try:
            Base.metadata.create_all(bind=engine)  # demo; Alembic preferred
            break
        except OperationalError:
            time.sleep(1)
    else:
        # after 30 retries, re-raise so logs show the real failure
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
