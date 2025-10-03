# NCHD Solver Drop-in

This archive adds:
- `backend/app/routers/groups.py`  (CRUD for /groups; stubbed if Group model is missing)
- `backend/app/routers/solve.py`   (stub endpoint for future solver preview)
- `backend/app/schemas/post.py`    (Pydantic schemas aligning with frontend)
- `backend/app/schemas/group.py`
- `backend/app/solver/{interfaces,constraints,calendar,allocations,engine}.py`
- `backend/app/services/activities.py`

## 1) Wire routers in your FastAPI app

Open `backend/app/main.py` and add these near your existing includes:

```python
from .routers import groups, solve  # NEW

app.include_router(groups.router)   # NEW
app.include_router(solve.router)    # NEW
```

> Keep your existing `app.include_router(api)` line.

## 2) Database models for Groups (optional)

If your `backend/app/models.py` does **not** yet define `Group` and `Activity`, the `/groups` router in this drop-in will run in *stub mode* (returns empty list and 501 for mutations). 
When you are ready to persist groups, add models (example skeleton):

```python
# in backend/app/models.py (example only)
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    rules = Column(JSON, default=dict)
    activities = relationship("Activity", back_populates="group", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    pattern = Column(JSON, nullable=False)  # {'kind':'weekly','weekday':'Mon','window':['13:00','17:00']} etc.
    site = Column(String, nullable=True)
    requires_supervisor = Column(Integer, default=0)
    group = relationship("Group", back_populates="activities")
```

Make sure your `seed.py` imports the models module (it already does), and that `Base.metadata.create_all(bind=engine)` is still called at startup (as in your `main.py`). For production, prefer Alembic.

## 3) Frontend env

Your nginx already proxies `/api/*` to backend. Frontend should call `/api/...`. The schemas in this drop-in mirror the earlier frontend model proposal.

## 4) Next steps

- Keep `/groups` stubbed or add models to persist.
- Implement real generators in `solver/allocations.py` and flesh out `constraints.py`.
- Extend `routers/solve.py` to invoke `Solver.preview_month(...)`.
