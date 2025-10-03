from __future__ import annotations
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from . import models

def seed(db: Session):
    """
    Idempotent-ish seed:
      - ensures at least 1 admin, 1 supervisor, 14 NCHDs
      - creates a couple of demo Posts with core_hours JSON
      - creates three Groups (on-call pool, teaching block, team)
      - links posts to the on-call pool by default
      - creates a small set of demo rota slots
    Safe to call on every startup.
    """

    # ---------------- Users ----------------
    # Create admin & supervisor if missing
    if db.query(models.User).filter(models.User.role == "admin").count() == 0:
        db.add(models.User(name="Admin 1", email="admin1@example.com", role="admin"))
    if db.query(models.User).filter(models.User.role == "supervisor").count() == 0:
        db.add(models.User(name="Supervisor 1", email="supervisor1@example.com", role="supervisor"))
    db.commit()

    # Ensure 14 NCHDs exist (create up to 14; keep existing if already present)
    nchd_existing = db.query(models.User).filter(models.User.role == "nchd").count()
    for i in range(nchd_existing, 14):
        db.add(models.User(name=f"NCHD {i+1}", email=f"nchd{i+1}@example.com", role="nchd"))
    db.commit()

    # Pool of users for demo rota allocation
    pool = db.query(models.User).all()

    # ---------------- Groups ----------------
    def get_or_create_group(name: str, kind: str, rules: dict):
        g = db.query(models.Group).filter(models.Group.name == name).first()
        if not g:
            g = models.Group(name=name, kind=kind, rules=rules or {})
            db.add(g)
            db.commit()
            db.refresh(g)
        return g

    on_call_pool = get_or_create_group(
        name="Newcastle 24h Pool",
        kind="on_call_pool",
        rules={"shift": "night", "hours": [["17:00", "09:00"]], "cap_per_month": 7}
    )
    teaching_block = get_or_create_group(
        name="Wednesday Teaching",
        kind="teaching_block",
        rules={"weekday": "Wed", "time": ["14:00", "16:00"]}
    )
    team_a = get_or_create_group(
        name="Team A (Clinics)",
        kind="team",
        rules={"clinic_days": ["Mon", "Thu"], "supervision": {"weekday": "Tue", "time": ["10:00", "11:00"]}}
    )

    # ---------------- Posts ----------------
    def get_or_create_post(title: str, site: str, grade: str, core_hours: dict, status: str = "ACTIVE_ROSTERABLE"):
        p = db.query(models.Post).filter(models.Post.title == title).first()
        if not p:
            p = models.Post(
                title=title,
                site=site,
                grade=grade,
                fte=1.0,
                status=status,
                core_hours=core_hours or {},
                eligibility={"call_policy": {"participates_in_call": True, "max_nights_per_month": 7, "min_rest_hours": 11, "role": "NCHD"}},
                notes=None,
            )
            db.add(p)
            db.commit()
            db.refresh(p)
        return p

    # Example core hours for demo
    mon_fri_9_5 = {"Mon": [["09:00", "17:00"]], "Tue": [["09:00", "17:00"]],
                   "Wed": [["09:00", "17:00"]], "Thu": [["09:00", "17:00"]], "Fri": [["09:00", "17:00"]]}

    p1 = get_or_create_post("Gen Adult 1", site="Newcastle", grade="Registrar", core_hours=mon_fri_9_5)
    p2 = get_or_create_post("Gen Adult 2", site="Newcastle", grade="Registrar", core_hours=mon_fri_9_5)

    # Link posts to groups if not already linked
    for p in (p1, p2):
        current_ids = {g.id for g in p.groups}
        to_add = []
        for g in (on_call_pool, teaching_block, team_a):
            if g.id not in current_ids:
                to_add.append(g)
        if to_add:
            p.groups.extend(to_add)
            db.commit()
            db.refresh(p)

    # ---------------- Demo rota slots ----------------
    # Keep the demo light; don’t regenerate if we already have many
    existing_slots = db.query(models.RotaSlot).count()
    if existing_slots < 40:
        start_base = datetime(2025, 1, 6, 9, 0)
        for d in range(10):  # ~2 weeks sample
            day = start_base + timedelta(days=d)

            # base day slot for p1
            base_end = day.replace(hour=17, minute=0)
            base_user = random.choice(pool)
            db.add(models.RotaSlot(
                user_id=base_user.id, post_id=p1.id,
                start=day, end=base_end, type="base", labels={"paid_break": "13:00-13:30"}
            ))

            # night call on p1
            nc_start = day.replace(hour=17, minute=0)
            nc_end = (day + timedelta(days=1)).replace(hour=9, minute=0)
            nc_user = random.choice(pool)
            db.add(models.RotaSlot(
                user_id=nc_user.id, post_id=p1.id,
                start=nc_start, end=nc_end, type="night_call", labels={}
            ))

        db.commit()
