from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import models, db_connection
from app.api import endpoints

# Initialize Database Tables
models.Base.metadata.create_all(bind=db_connection.engine)

# Create FastAPI app
app = FastAPI(
    title="ClinMatch AI - Clinical Trial Eligibility Decision Support",
    description="AI-powered patient-trial matching system with NLP and rule-based logic",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(endpoints.router, prefix="/api", tags=["API"])

@app.get("/")
def home():
    """Root endpoint"""
    return {
        "message": "ClinMatch AI Backend is Running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("ClinMatch AI Server Started")
    print("Database initialized")
    print("Ready to process clinical trial data")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("ClinMatch AI Server Stopped")
