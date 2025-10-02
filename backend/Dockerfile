# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Build context is the REPO ROOT (.. in compose). Copy from backend/...
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
#COPY backend/alembic.ini ./alembic.ini   #May need to uncomment if alembic needed
#COPY backend/migrations ./migrations      #May need to uncomment if alembic needed

ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
