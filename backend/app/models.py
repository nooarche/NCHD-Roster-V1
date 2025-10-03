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
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # "on_call_pool" | "teaching_block" | "team" | ...
    rules = Column(JSONB, default=dict)    # rule payload for that group
    posts = relationship("Post", secondary="post_groups", back_populates="groups")

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
