import jwt
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict
from .config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MIN, REFRESH_TOKEN_EXPIRE_DAYS
from .redis_client import get_redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with JTI for revocation support.

    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)

    # Add JTI (JWT ID) for token revocation
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": jti,
        "iat": datetime.utcnow()
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with JTI for revocation support.

    Args:
        data: Token payload data

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Add JTI (JWT ID) for token revocation
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": jti,
        "iat": datetime.utcnow()
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT token.
    Checks token revocation if Redis is available.

    Args:
        token: JWT token string

    Returns:
        Token payload dict or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if token has been revoked (if Redis is available)
        jti = payload.get("jti")
        if jti:
            redis_client = get_redis()
            if redis_client.is_token_revoked(jti):
                return None

        return payload
    except jwt.PyJWTError:
        return None


def revoke_token(token: str) -> bool:
    """
    Revoke a JWT token by adding it to the revocation list.

    Args:
        token: JWT token string to revoke

    Returns:
        True if successful, False otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            return False

        # Calculate remaining TTL
        expires_at = datetime.fromtimestamp(exp)
        remaining = int((expires_at - datetime.utcnow()).total_seconds())

        if remaining <= 0:
            return True  # Token already expired

        redis_client = get_redis()
        return redis_client.revoke_token(jti, remaining)

    except jwt.PyJWTError:
        return False