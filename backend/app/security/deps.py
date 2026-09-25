from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import User
from app.security.auth import decode_token
from app.utils.constants import ADMIN_ROLES, GOVERNMENT_ROLES, INDUSTRY_ROLES, UNIVERSITY_ROLES

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    payload = decode_token(creds.credentials)
    if not payload or payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, int(payload.get("sub", 0)))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")
    return user


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if not creds:
        return None
    payload = decode_token(creds.credentials)
    if not payload:
        return None
    return db.get(User, int(payload.get("sub", 0)))


def require_roles(*roles: str):
    def _inner(user: User = Depends(get_current_user)) -> User:
        allowed = set(roles)
        if user.primary_role not in allowed and user.primary_role not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="You do not have permission for this action")
        if user.verification_status not in {"verified", "activated"} and user.primary_role not in ADMIN_ROLES:
            if user.primary_role != "citizen" or user.verification_status not in {
                "pending_verification",
                "verified",
                "activated",
            }:
                if user.primary_role != "citizen":
                    raise HTTPException(
                        status_code=403,
                        detail="Account is not yet verified. Access is restricted until approval.",
                    )
        return user

    return _inner


def require_verified_org(user: User = Depends(get_current_user)) -> User:
    if user.primary_role in ADMIN_ROLES:
        return user
    if user.verification_status not in {"verified", "activated"}:
        raise HTTPException(status_code=403, detail="Organization account is pending verification")
    return user


def client_meta(request: Request) -> tuple[str, str]:
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent", "")[:250]
    return ip, ua


def is_gov(user: User) -> bool:
    return user.primary_role in GOVERNMENT_ROLES or user.primary_role in ADMIN_ROLES


def is_university(user: User) -> bool:
    return user.primary_role in UNIVERSITY_ROLES or user.primary_role in ADMIN_ROLES


def is_industry(user: User) -> bool:
    return user.primary_role in INDUSTRY_ROLES or user.primary_role in ADMIN_ROLES
