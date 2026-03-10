from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.auth_schema import UserCreate, UserLogin
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def signup_user(self, db: Session, user_in: UserCreate) -> User:
        if db.query(User).filter(User.email == user_in.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email already registered"
            )
        
        db_user = User(
            email=user_in.email,
            name=user_in.full_name or user_in.email.split('@')[0],
            hashed_password=get_password_hash(user_in.password)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(self, db: Session, login_data: UserLogin) -> User:
        user = db.query(User).filter(User.email == login_data.email).first()
        
        is_valid = False
        if user:
            try:
                is_valid = verify_password(login_data.password, user.hashed_password)
            except Exception as err:
                logger.warning(f"Password verification error for {login_data.email}: {err}")
                is_valid = False

        if not user or not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )
        
        return user

    def generate_token_data(self, user: User) -> dict:
        token = create_access_token({"sub": user.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "full_name": user.name,
                "id": str(user.id)
            }
        }

auth_service = AuthService()
