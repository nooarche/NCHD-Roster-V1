from sqlalchemy.orm import Session
from . import models
from datetime import datetime, timedelta
import random

def seed(db: Session):
    # don't double-seed if users already exist
    if db.query(models.User).count() > 0:
        return

    # --- Users ---
    admin = models.User(name="Admin 1", email="admin1@example.com", role="admin")
    supervisor = models.User(name="Supervisor 1", email="supervisor1@example.com", role="supervisor")
    db.add_all([admin, supervisor]); db.commit()

    nchds = []
    for i in range(14):  # NCHD 1..14
        u = models.User(name=f"NCHD {i+1}", email=f"nchd{i+1}@example.com", role="nchd")
        nchds.append(u)
        db.add(u)
    db.commit()

    # --- Posts ---
    p1 = models.Post(title="Gen Adult 1", opd_day="Wed")
    p2 = models.Post(title="Gen Adult 2", opd_day="Tue")
    db.add_all([p1, p2]); db.commit()

    # --- Demo rota slots (approx 224) ---
    start_base = datetime(2025, 1, 6, 9, 0)
    pool = [admin, supervisor] + nchds  # random assignment for demo
    for d in range(28):  # ~4 weeks
        day = start_base + timedelta(days=d)
        # base slot
        end = day.replace(hour=17, minute=0)
        slot = models.RotaSlot(
            user_id=random.choice(pool).id, post_id=p1.id,
            start=day, end=end, type="base", labels={"paid_break": "13:00-13:30"}
        )
        db.add(slot)

        # night call
        nc_start = day.replace(hour=17, minute=0)
        nc_end = (day + timedelta(days=1)).replace(hour=9, minute=0)
        slot2 = models.RotaSlot(
            user_id=random.choice(pool).id, post_id=p1.id,
            start=nc_start, end=nc_end, type="night_call", labels={}
        )
        db.add(slot2)

    db.commit()
