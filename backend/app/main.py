
from fastapi import FastAPI
from .routers import api
from .db import engine, Base, SessionLocal
from .seed import seed

app = FastAPI(title="NCHD Rostering & Leave System API", version="0.1.0")
app.include_router(api)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # for demo (alembic is preferred)
    # Seed demo data
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
