# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String)
    role = Column(String, default="nchd")  # "nchd" | "supervisor" | "admin" | "staff"
    grade = Column(String)
    site = Column(String)
    active = Column(Boolean, default=True)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)

    site = Column(String)
    grade = Column(String)
    fte = Column(Float, default=1.0)
    status = Column(String, default="ACTIVE_ROSTERABLE")  # or "VACANT_UNROSTERABLE"

    # flexible JSON stores for rules and working patterns
    core_hours = Column(JSONB, default=dict)   # e.g. {"Mon":[["09:00","17:00"]], ...}
    eligibility = Column(JSONB, default=dict)  # e.g. {"call_policy":{...}}
    notes = Column(String)

    # many-to-many to Group
    groups = relationship("Group", secondary="post_groups", back_populates="posts")


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)   # e.g. on_call_pool | protected_teaching | clinic_team
    rules = Column(JSON, nullable=False, default=dict)

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)   # weekly | one_off
    pattern = Column(JSON, nullable=False, default=dict)
    group = relationship("Group", backref="activities")
    
class PostGroup(Base):
    __tablename__ = "post_groups"
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)

class RotaSlot(Base):
    __tablename__ = "rota_slots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    type = Column(String, default="night_call")  # night_call / day / evening / etc.
    labels = Column(JSONB, default=dict)

# ===[ANCHOR: GROUPS_ACTIVITIES_MODELS]========================================
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import relationship

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # e.g. on_call_pool, protected_teaching, clinic_team
    rules = Column(JSON, nullable=False, default=dict)

    # Optional link: which posts belong to this group (M2M would be better later)
    # For now we keep groups independent; you’ll associate via rules or future table.

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # weekly | one_off
    # weekly pattern like {"byweekday":["MON"],"start":"12:30","end":"13:30"}
    # one_off like {"start":"2025-11-10T12:30:00","end":"2025-11-10T13:30:00"}
    pattern = Column(JSON, nullable=False, default=dict)

    group = relationship("Group", backref="activities")
# =============================================================================
