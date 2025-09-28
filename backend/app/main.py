from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from .routers import api
from .db import engine, Base, SessionLocal
from .seed import seed

app = FastAPI(title="NCHD Rostering & Leave System API", version="0.1.0")


# --- CORS allow localhost dev ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------

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
