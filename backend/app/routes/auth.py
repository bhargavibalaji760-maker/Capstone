from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime
import logging

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.auth_schema import UserCreate, UserLogin
from app.db.session import get_db
from app.db.models import User
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token payload missing 'sub' claim")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"User in token not found in DB: {email}")
        raise credentials_exception
    return user


@router.post("/signup")
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = auth_service.signup_user(db, user_in)
        token_data = auth_service.generate_token_data(db_user)
        
        response = JSONResponse(content=token_data)
        response.set_cookie(
            key="access_token", 
            value=token_data["access_token"], 
            httponly=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate_user(db, login_data)
        token_data = auth_service.generate_token_data(user)
        
        response = JSONResponse(content=token_data)
        response.set_cookie(
            key="access_token", 
            value=token_data["access_token"], 
            httponly=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
def logout():
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="access_token", samesite="lax")
    return response
