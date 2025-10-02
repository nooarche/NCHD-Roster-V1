import sqlalchemy as sa
from sqlalchemy.orm import relationship
from .db import Base

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Text, Date, Float

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    site = Column(String(100))             # e.g., "Wicklow CMHT"
    grade = Column(String(32))             # e.g., "Registrar", "SHO"
    fte = Column(Float, default=1.0)       # Full-Time Equivalent (0.1–1.0)
    status = Column(String(32), default="ACTIVE_ROSTERABLE")  # ACTIVE_ROSTERABLE | VACANT_ROSTERABLE | VACANT_UNROSTERABLE

    # OPD and supervision/teaching & core hours templates as JSON for now
    opd = Column(JSON, nullable=True)          # {"days": ["Mon","Thu"], "guard": true, "sessions": {"Mon":[["09:30","12:30"]]}}
    teaching = Column(JSON, nullable=True)     # {"protected":[{"dow":"Wed","start":"14:00","end":"16:30","ph_rule":"NA_NO_COMP"}]}
    supervision = Column(JSON, nullable=True)  # {"academic":{"mins":60,"pref":{"dow":"Thu","time":"15:00"}},
                                               #  "clinical":{"mins":60,"on_opd_days":True}}
    core_hours = Column(JSON, nullable=True)   # {"Mon-Thu":{"start":"09:00","end":"17:00","break":["13:00","13:30"]},
                                               #  "Fri":{"start":"09:00","end":"16:00","break":["13:00","13:30"]}}
    eligibility = Column(JSON, nullable=True)  # {"day_call":True,"night_call":True,"weekend":True,"ph":True,"notes":""}
    notes = Column(Text)

    vacancy_windows = relationship("VacancyWindow", back_populates="post", cascade="all, delete-orphan")

class VacancyWindow(Base):
    __tablename__ = "vacancy_windows"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    status = Column(String(32), nullable=False)      # VACANT_ROSTERABLE | VACANT_UNROSTERABLE
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)           # null = open-ended

    post = relationship("Post", back_populates="vacancy_windows")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(32), nullable=False)  # admin, supervisor, nchd, staff
    created_at = Column(DateTime)



class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    observed = Column(Boolean, default=True)

class RotaSlot(Base):
    __tablename__ = "rota_slots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    type = Column(String(32), nullable=False)  # base, day_call, night_call, teaching, supervision, handover, leave
    labels = Column(JSON)

class Leave(Base):
    __tablename__ = "leave"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    type = Column(String(32), nullable=False)  # annual, study, sick, etc.
    reason = Column(String(255))
    status = Column(String(16), default="approved")

class Teaching(Base):
    __tablename__ = "teaching"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    topic = Column(String(255))

class Supervision(Base):
    __tablename__ = "supervision"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    type = Column(String(32), nullable=False)  # academic or clinical

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    level = Column(String(16), nullable=False)  # info, warning, critical
    message = Column(String(255), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"))
    slot_id = Column(Integer, ForeignKey("rota_slots.id"))
    created_at = Column(DateTime)
    resolved_at = Column(DateTime)

class Audit(Base):
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(64), nullable=False)
    before = Column(JSON)
    after = Column(JSON)
    reason = Column(String(255))
    created_at = Column(DateTime)

# models.py (new)
class Team(Base):
    __tablename__ = "teams"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), unique=True, nullable=False)
    supervisor_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=True)  # consultant

class Contract(Base):
    __tablename__ = "contracts"
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    post_id = sa.Column(sa.Integer, sa.ForeignKey("posts.id"), nullable=False)
    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"), nullable=True)  # inferred from post/team if you like
    start = sa.Column(sa.Date, nullable=False)
    end = sa.Column(sa.Date, nullable=True)  # open-ended (e.g., supervisors)

class TeamMember(Base):
    __tablename__ = "team_members"
    id = sa.Column(sa.Integer, primary_key=True)
    team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    role = sa.Column(sa.String(32), nullable=False, default="nchd")  # or "supervisor", "staff"

# Core hours & policy
class CoreHoursProfile(Base):
    __tablename__ = "core_hours_profiles"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False)
    weekly_hours = sa.Column(sa.Integer, nullable=False)  # e.g., 39
    policy_json = sa.Column(sa.JSON, nullable=False, default=dict)  # OPD rules, rest rules, etc.

class CoreHoursOverride(Base):
    __tablename__ = "core_hours_overrides"
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    start = sa.Column(sa.Date, nullable=False)
    end = sa.Column(sa.Date, nullable=True)
    weekly_hours = sa.Column(sa.Integer, nullable=False)  # personal override

class OPDSession(Base):
    __tablename__ = "opd_sessions"
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    day_of_week = sa.Column(sa.Integer, nullable=False)  # 0=Mon..6=Sun
    start_time = sa.Column(sa.Time, nullable=False)
    end_time = sa.Column(sa.Time, nullable=False)
    within_core = sa.Column(sa.Boolean, default=True)

class SupervisionSlot(Base):
    __tablename__ = "supervision_slots"
    id = sa.Column(sa.Integer, primary_key=True)
    supervisor_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    nchd_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    day_of_week = sa.Column(sa.Integer, nullable=False)
    start_time = sa.Column(sa.Time, nullable=False)
    end_time = sa.Column(sa.Time, nullable=False)
