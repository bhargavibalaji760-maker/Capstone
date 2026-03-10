from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError

from app.core.config import settings, ensure_default_admin
from app.db.session import engine, Base
from app.db import models # Pre-load models for metadata
from app.routes import auth, patients, trials, matching, dashboard, pages

import os
import logging

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="MediTrial AI", version="1.1.0")

# ================= EXCEPTION HANDLERS =================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"422 Validation Error on {request.url}: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "body": str(exc.body)[:500]})

# ================= CORS CONFIGURATION =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= CUSTOM OPENAPI =================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["BearerAuth"] = {"type": "http", "scheme": "bearer"}
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

# ================= STATIC ASSETS =================
# Calculate paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.getenv("FRONTEND_DIR", os.path.join(BASE_DIR, "frontend"))
if FRONTEND_DIR == "/frontend":
    FRONTEND_DIR = "/app/frontend"

# Mount static assets
if os.path.exists(FRONTEND_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

# ================= ROUTER MOUNTING =================
API = settings.API_V1_STR
app.include_router(auth.router, prefix=f"{API}/auth", tags=["Identity"])
app.include_router(patients.router, prefix=f"{API}/patients", tags=["Clinical Records"])
app.include_router(trials.router, prefix=f"{API}/trials", tags=["Protocol Registry"])
app.include_router(matching.router, prefix=f"{API}/matching", tags=["Intelligence Pipeline"])
app.include_router(dashboard.router, prefix=f"{API}/dashboard", tags=["Analytics"])

# UI Delivery (Templates & Static Pages)
app.include_router(pages.router)

# ================= LIFECYCLE EVENTS =================
@app.on_event("startup")
def startup_event():
    # Ensure tables exist
    logger.info("Initializing clinical database schema...")
    Base.metadata.create_all(bind=engine)
    
    ensure_default_admin()
    logger.info("🚀 MediTrial AI Infrastructure Online (Port 3000)")