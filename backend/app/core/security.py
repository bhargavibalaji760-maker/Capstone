from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_to_bcrypt_limit(password: str, limit: int = 72) -> str:
    """Truncate a string so its UTF-8 encoding is at most `limit` bytes.

    bcrypt only accepts passwords up to 72 bytes. This helper ensures
    we consistently truncate before hashing or verification.
    """
    if password is None:
        return password
    encoded = password.encode("utf-8", errors="ignore")
    if len(encoded) <= limit:
        return password
    truncated = encoded[:limit]
    # decode ignoring incomplete trailing byte sequences
    return truncated.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Truncate the plaintext to bcrypt's 72-byte limit before verification.
    """
    truncated = _truncate_to_bcrypt_limit(plain_password)
    return pwd_context.verify(truncated, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    truncated = _truncate_to_bcrypt_limit(password)
    hashed = pwd_context.hash(truncated)
    if isinstance(hashed, bytes):
        return hashed.decode("utf-8")
    return hashed


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    if isinstance(encoded_jwt, bytes):
        return encoded_jwt.decode("utf-8")
    return encoded_jwt


def decode_token(token: str) -> str | None:
    """Decode a JWT access token and return the `sub` (email) or None on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None
