import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 180_000)
    return f"pbkdf2${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = stored.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2":
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 180_000)
    return hmac.compare_digest(check.hex(), digest)


def create_token(data: dict, expires_minutes: int | None = None, refresh: bool = False) -> str:
    payload = data.copy()
    minutes = expires_minutes or (
        settings.JWT_REFRESH_EXPIRE_MINUTES if refresh else settings.JWT_EXPIRE_MINUTES
    )
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload["typ"] = "refresh" if refresh else "access"
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
