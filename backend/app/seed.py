
from sqlalchemy.orm import Session
from . import models
from datetime import datetime, timedelta
import random

def seed(db: Session):
    if db.query(models.User).count() > 0:
        return

    # 15 users
    users = []
    for i in range(15):
        u = models.User(name=f"NCHD {i+1}", email=f"user{i+1}@example.com", role="nchd" if i>1 else ("admin" if i==0 else "supervisor"))
        users.append(u)
        db.add(u)
    db.commit()

    # 2 posts
    p1 = models.Post(title="Gen Adult 1", opd_day="Wed")
    p2 = models.Post(title="Gen Adult 2", opd_day="Tue")
    db.add_all([p1, p2]); db.commit()

    # generate ~224 shifts over a few weeks (demo only)
    start_base = datetime(2025, 1, 6, 9, 0)
    for d in range(28):  # 4 weeks
        day = start_base + timedelta(days=d)
        # base slot
        end = day.replace(hour=17, minute=0)
        slot = models.RotaSlot(user_id=random.choice(users).id, post_id=p1.id, start=day, end=end, type="base", labels={"paid_break": "13:00-13:30"})
        db.add(slot)

        # simple night call every day
        nc_start = day.replace(hour=17, minute=0)
        nc_end = (day + timedelta(days=1)).replace(hour=9, minute=0)
        slot2 = models.RotaSlot(user_id=random.choice(users).id, post_id=p1.id, start=nc_start, end=nc_end, type="night_call", labels={})
        db.add(slot2)

    db.commit()
