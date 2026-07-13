import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from passlib.context import CryptContext

from .config import ACCESS_TOKEN_EXPIRE_MIN, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    A malformed/unparseable stored hash is treated as a failed verification
    (returns False) rather than propagating an exception, so callers such as
    login never surface a 500 for a corrupt hash (GH#673).
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        # passlib raises UnknownHashError (a ValueError subclass) for an
        # unrecognizable hash, and TypeError if the stored value is not a str.
        return False


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
    to_encode.update({"exp": expire, "type": "access", "jti": jti, "iat": datetime.utcnow()})

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
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti, "iat": datetime.utcnow()})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT token.
    Token revocation is checked via database in dependencies.py.

    Args:
        token: JWT token string

    Returns:
        Token payload dict or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
