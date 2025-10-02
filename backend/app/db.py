# backend/app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Use your existing env var if provided; otherwise default stays as you had it
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://roster:roster@localhost:5432/rosterdb"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# IMPORTANT: define declarative_base() exactly once in the whole app
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
