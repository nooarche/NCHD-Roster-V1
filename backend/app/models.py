# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Date, JSON
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

    core_hours = Column(JSONB, default=dict)   # e.g. {"Mon":[["09:00","17:00"]], ...}
    eligibility = Column(JSONB, default=dict)  # e.g. {"call_policy":{...}}
    notes = Column(String)

    groups = relationship("Group", secondary="post_groups", back_populates="posts")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)   # e.g. on_call_pool | protected_teaching | clinic_team
    rules = Column(JSON, nullable=False, default=dict)

    posts = relationship("Post", secondary="post_groups", back_populates="groups")
    activities = relationship("Activity", back_populates="group", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)   # weekly | one_off
    pattern = Column(JSON, nullable=False, default=dict)
    group = relationship("Group", back_populates="activities")

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
