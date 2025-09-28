
from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../app")

config = context.config
fileConfig(config.config_file_name)

from app.db import Base  # noqa: E402
from app import models  # noqa: F401,E402

def run_migrations_offline():
    url = os.environ.get("DATABASE_URL")
    context.configure(
        url=url, target_metadata=Base.metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": os.environ.get("DATABASE_URL")},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
