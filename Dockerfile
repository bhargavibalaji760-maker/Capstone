FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev

# 1. Copy Backend Requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy Backend Code
COPY backend/app /app/app

# 3. Copy Frontend Code
COPY frontend /app/frontend

ENV PYTHONPATH=/app

EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]