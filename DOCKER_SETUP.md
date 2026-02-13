# Docker Deployment Guide - ClinMatch AI

## Prerequisites
- Docker installed
- Docker Compose installed

## Setup & Deployment

### 1. Build and run all services
```bash
docker-compose up --build
```

### 2. Access the application
- **Main Dashboard**: http://localhost
- **API Documentation**: http://localhost/api/docs
- **API (direct)**: http://localhost:8000

### 3. View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f streamlit
docker-compose logs -f nginx
```

### 4. Stop services
```bash
docker-compose down
```

### 5. Rebuild after code changes
```bash
docker-compose up --build
```

## Architecture

```
┌─────────────────────────────────────────┐
│         External User (Port 80)         │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│          Nginx Reverse Proxy             │
│         (docker-compose-nginx)          │
└───────────┬──────────────────────┬──────┘
            │                      │
    ┌───────▼────────┐   ┌────────▼──────┐
    │  FastAPI       │   │   Streamlit   │
    │  Backend       │   │   Frontend    │
    │  :8000         │   │   :8501       │
    │ (API routes)   │   │ (UI routes)   │
    └────────────────┘   └───────────────┘
```

## Routing Rules

- **`/`** → Streamlit Dashboard
- **`/api/`** → FastAPI Backend API
- **`/health`** → Backend Health Check
- **`/_stcore/stream`** → Streamlit WebSocket

## Troubleshooting

### Port already in use
```bash
# Change port in docker-compose.yml
# Change "80:80" to "8080:80" for nginx
```

### Container connection issues
```bash
# Verify network
docker network ls
docker network inspect clinmatch-network
```

### Clear everything and restart
```bash
docker-compose down -v
docker-compose up --build
```
