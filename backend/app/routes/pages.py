from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

# Calculate paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.getenv("FRONTEND_DIR", os.path.join(BASE_DIR, "frontend"))
if FRONTEND_DIR == "/frontend":
    FRONTEND_DIR = "/app/frontend"

templates = Jinja2Templates(directory=FRONTEND_DIR)

# ─── Public static pages ───
@router.get("/", include_in_schema=False)
def root(request: Request):
    return templates.TemplateResponse("pages/index.html", {"request": request})

@router.get("/login.html", include_in_schema=False)
@router.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "pages/login.html"))

@router.get("/signup.html", include_in_schema=False)
@router.get("/signup", include_in_schema=False)
def signup_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "pages/signup.html"))

# ─── Internal pages — rendered via Jinja2 (template inheritance) ───
@router.get("/home", include_in_schema=False)
@router.get("/home.html", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse("pages/home.html", {"request": request})

@router.get("/dashboard", include_in_schema=False)
@router.get("/dashboard.html", include_in_schema=False)
def dashboard(request: Request):
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})

@router.get("/patients", include_in_schema=False)
@router.get("/patients.html", include_in_schema=False)
def patients(request: Request):
    return templates.TemplateResponse("pages/patients.html", {"request": request})

@router.get("/trials", include_in_schema=False)
@router.get("/trials.html", include_in_schema=False)
def trials_page(request: Request):
    return templates.TemplateResponse("pages/trials.html", {"request": request})

@router.get("/matches", include_in_schema=False)
@router.get("/matches.html", include_in_schema=False)
def matches(request: Request):
    return templates.TemplateResponse("pages/matches.html", {"request": request})

@router.get("/profile", include_in_schema=False)
@router.get("/profile.html", include_in_schema=False)
def profile(request: Request):
    return templates.TemplateResponse("pages/profile.html", {"request": request})
