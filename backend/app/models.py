# backend/app/models.py

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    ForeignKey, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

# IMPORTANT: use the single Base defined in db.py so all models share one metadata
from .db import Base


# -------------------------
# Users
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String)
    role = Column(String, default="nchd")  # "nchd" | "supervisor" | "admin" | "staff"
    grade = Column(String)
    site = Column(String)
    active = Column(Boolean, default=True)


# -------------------------
# Posts
# -------------------------
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)

    site = Column(String)
    grade = Column(String)
    fte = Column(Float, default=1.0)
    status = Column(String, default="ACTIVE_ROSTERABLE")  # or "VACANT_UNROSTERABLE"

    # Flexible JSON stores for rules and working patterns
    # e.g. core_hours: {"Mon":[["09:00","17:00"]], "Fri":[["09:00","16:00"]]}
    core_hours = Column(JSONB, default=dict, nullable=True)

    # e.g. eligibility: {"call_policy": {...}}
    eligibility = Column(JSONB, default=dict, nullable=True)

    notes = Column(String)

    # many-to-many to Group via association table "post_groups"
    groups = relationship("Group", secondary="post_groups", back_populates="posts")


# -------------------------
# Groups
# -------------------------
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)   # e.g. on_call_pool | protected_teaching | clinic_team

    # Arbitrary rules payload for the group
    # (kept as JSONB for Postgres efficiency/consistency)
    rules = Column(JSONB, default=dict, nullable=True)

    # back-reference of M2M from Post
    posts = relationship("Post", secondary="post_groups", back_populates="groups")

    # one-to-many Activities
    activities = relationship("Activity", back_populates="group", cascade="all, delete-orphan")


# -------------------------
# Activities (belong to a Group)
# -------------------------
class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # "weekly" | "one_off"

    # For weekly:
    #   {"byweekday":["MON"], "start":"12:30", "end":"13:30"}
    # For one_off:
    #   {"start":"2025-11-10T12:30:00", "end":"2025-11-10T13:30:00"}
    pattern = Column(JSONB, default=dict, nullable=False)

    group = relationship("Group", back_populates="activities")


# -------------------------
# Post <-> Group (association)
# -------------------------
class PostGroup(Base):
    __tablename__ = "post_groups"

    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)


# -------------------------
# Rota slots
# -------------------------
class RotaSlot(Base):
    __tablename__ = "rota_slots"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)

    # e.g. "night_call" / "day" / "evening" / etc.
    type = Column(String, default="night_call")

    # free-form labels for extra tagging
    labels = Column(JSONB, default=dict, nullable=True)
