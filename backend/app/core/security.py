from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Initialize HTTPBearer security scheme
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to verify the Bearer token.
    For this prototype, any non-empty token is accepted.
    Real implementation would verify JWT tokens.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Sample token check (e.g., 'clinmatch-secure-2026')
    # For now, we allow any token to enable easy testing in Swagger
    return {"user": "clinician", "token": token}
