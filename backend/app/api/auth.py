import json
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import (
    Citizen,
    GovernmentDepartment,
    GovernmentUser,
    Industry,
    IndustryCapability,
    Role,
    University,
    UniversityDepartment,
    User,
    UserRole,
    UserVerification,
)
from app.schemas import (
    CitizenRegisterIn,
    GovernmentRegisterIn,
    IndustryRegisterIn,
    LoginIn,
    TokenOut,
    UniversityRegisterIn,
    VerifyIn,
)
from app.security.auth import create_token, hash_password, verify_password
from app.security.deps import client_meta, get_current_user
from app.services.audit import AuditLogService
from app.services.notifications import NotificationService
from app.utils.constants import ADMIN_ROLES

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _password_ok(password: str) -> bool:
    return bool(re.search(r"[A-Za-z]", password) and re.search(r"\d", password) and len(password) >= 8)


def _mobile_ok(mobile: str) -> bool:
    digits = re.sub(r"\D", "", mobile)
    return len(digits) == 10


def _issue_tokens(user: User) -> TokenOut:
    access = create_token({"sub": str(user.id), "role": user.primary_role})
    refresh = create_token({"sub": str(user.id), "role": user.primary_role}, refresh=True)
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        role=user.primary_role,
        verification_status=user.verification_status,
        full_name=user.full_name,
        user_id=user.id,
    )


def _ensure_unique_email(db: Session, email: str):
    if db.query(User).filter(User.email == email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")


def _attach_role(db: Session, user: User, role_name: str):
    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))


def _make_code() -> str:
    return "123456"  # demo/dev verification; replace SMTP provider in production


@router.post("/register/citizen", response_model=TokenOut)
def register_citizen(payload: CitizenRegisterIn, request: Request, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not _password_ok(payload.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters and include letters and numbers")
    if not _mobile_ok(payload.mobile):
        raise HTTPException(status_code=400, detail="Enter a valid 10-digit mobile number")
    _ensure_unique_email(db, payload.email)
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        mobile=payload.mobile,
        primary_role="citizen",
        verification_status="pending_verification",
    )
    db.add(user)
    db.flush()
    db.add(
        Citizen(
            user_id=user.id,
            district=payload.district,
            block=payload.block,
            village=payload.village,
            address=payload.address,
        )
    )
    _attach_role(db, user, "citizen")
    code = _make_code()
    db.add(
        UserVerification(
            user_id=user.id,
            channel="email",
            code=code,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
    )
    ip, ua = client_meta(request)
    AuditLogService.log(db, "CREATE", "user", str(user.id), user, details="Citizen registered", ip_address=ip, user_agent=ua)
    NotificationService.notify_role(
        db, "admin", "registration", "New citizen registration", f"{user.full_name} registered as citizen", "user", str(user.id)
    )
    db.commit()
    db.refresh(user)
    return _issue_tokens(user)


@router.post("/register/university")
def register_university(payload: UniversityRegisterIn, request: Request, db: Session = Depends(get_db)):
    _ensure_unique_email(db, payload.email)
    if not _password_ok(payload.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters and include letters and numbers")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.contact_person,
        mobile=payload.phone,
        primary_role="university",
        verification_status="pending_verification",
    )
    db.add(user)
    db.flush()
    uni = University(
        user_id=user.id,
        name=payload.name,
        institution_type=payload.institution_type,
        official_id=payload.official_id,
        address=payload.address,
        district=payload.district,
        website=payload.website,
        contact_person=payload.contact_person,
        phone=payload.phone,
        faculty_expertise=payload.faculty_expertise,
        research_areas=payload.research_areas,
        laboratories=payload.laboratories,
        innovation_centre=payload.innovation_centre,
        incubation_centre=payload.incubation_centre,
        previous_projects=payload.previous_projects,
        technologies=payload.technologies,
        verification_status="pending_verification",
    )
    db.add(uni)
    db.flush()
    for name in [d.strip() for d in payload.departments.split(",") if d.strip()]:
        db.add(UniversityDepartment(university_id=uni.id, name=name))
    _attach_role(db, user, "university")
    ip, ua = client_meta(request)
    AuditLogService.log(db, "CREATE", "university", str(uni.id), user, details="University registration submitted", ip_address=ip, user_agent=ua)
    NotificationService.notify_role(db, "admin", "registration", "University registration pending", payload.name, "university", str(uni.id))
    db.commit()
    return {"message": "Registration submitted. Admin verification is required before access is granted.", "status": "pending_verification"}


@router.post("/register/industry")
def register_industry(payload: IndustryRegisterIn, request: Request, db: Session = Depends(get_db)):
    _ensure_unique_email(db, payload.email)
    role = payload.organization_type if payload.organization_type in {"industry", "startup", "msme", "csr"} else "industry"
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.contact_person,
        mobile=payload.phone,
        primary_role=role,
        verification_status="pending_verification",
    )
    db.add(user)
    db.flush()
    org = Industry(
        user_id=user.id,
        company_name=payload.company_name,
        organization_type=role,
        sector=payload.sector,
        registration_details=payload.registration_details,
        website=payload.website,
        address=payload.address,
        district=payload.district,
        contact_person=payload.contact_person,
        phone=payload.phone,
        technical_expertise=payload.technical_expertise,
        products_services=payload.products_services,
        technologies=payload.technologies,
        csr_areas=payload.csr_areas,
        verification_status="pending_verification",
    )
    db.add(org)
    db.flush()
    for name, enabled in [
        ("funding", payload.funding_capability),
        ("mentorship", payload.mentorship_capability),
        ("prototype", payload.prototype_capability),
        ("testing", payload.testing_capability),
        ("deployment", payload.deployment_capability),
    ]:
        db.add(IndustryCapability(industry_id=org.id, name=name, enabled=enabled))
    _attach_role(db, user, role)
    ip, ua = client_meta(request)
    AuditLogService.log(db, "CREATE", "industry", str(org.id), user, details="Industry registration submitted", ip_address=ip, user_agent=ua)
    NotificationService.notify_role(db, "admin", "registration", "Industry registration pending", payload.company_name, "industry", str(org.id))
    db.commit()
    return {"message": "Registration submitted. Admin verification is required before access is granted.", "status": "pending_verification"}


@router.post("/register/government")
def register_government(payload: GovernmentRegisterIn, request: Request, db: Session = Depends(get_db)):
    _ensure_unique_email(db, payload.email)
    dept = None
    if payload.department_code:
        dept = db.query(GovernmentDepartment).filter(GovernmentDepartment.code == payload.department_code).first()
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        mobile=payload.mobile,
        primary_role="government_officer",
        verification_status="pending_verification",
    )
    db.add(user)
    db.flush()
    db.add(
        GovernmentUser(
            user_id=user.id,
            official_id=payload.official_id,
            designation=payload.designation,
            department_id=dept.id if dept else None,
            district=payload.district,
            jurisdiction=payload.jurisdiction,
        )
    )
    _attach_role(db, user, "government_officer")
    ip, ua = client_meta(request)
    AuditLogService.log(db, "CREATE", "government_user", str(user.id), user, details="Government registration submitted", ip_address=ip, user_agent=ua)
    NotificationService.notify_role(db, "admin", "registration", "Government officer registration pending", payload.full_name, "user", str(user.id))
    db.commit()
    return {"message": "Official verification is required before government access is granted.", "status": "pending_verification"}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is suspended")
    user.last_login_at = datetime.now(timezone.utc)
    ip, ua = client_meta(request)
    AuditLogService.log(db, "LOGIN", "user", str(user.id), user, ip_address=ip, user_agent=ua)
    db.commit()
    return _issue_tokens(user)


@router.post("/verify")
def verify(payload: VerifyIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    rec = (
        db.query(UserVerification)
        .filter(UserVerification.user_id == user.id, UserVerification.consumed.is_(False))
        .order_by(UserVerification.id.desc())
        .first()
    )
    if not rec or rec.code != payload.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    if rec.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code expired")
    rec.consumed = True
    user.verification_status = "activated"
    NotificationService.notify_user(db, user.id, "account", "Account activated", "Your citizen account is now active.", "user", str(user.id))
    db.commit()
    return {"message": "Account activated", "status": user.verification_status}


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    extra = {}
    if user.citizen:
        extra["citizen"] = {
            "district": user.citizen.district,
            "block": user.citizen.block,
            "village": user.citizen.village,
            "address": user.citizen.address,
        }
    if user.university:
        extra["university_id"] = user.university.id
        extra["university_name"] = user.university.name
    if user.industry:
        extra["industry_id"] = user.industry.id
        extra["company_name"] = user.industry.company_name
    if user.government_profile:
        extra["department_id"] = user.government_profile.department_id
        extra["official_id"] = user.government_profile.official_id
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "mobile": user.mobile,
        "primary_role": user.primary_role,
        "verification_status": user.verification_status,
        "is_demo": user.is_demo,
        "is_admin": user.primary_role in ADMIN_ROLES,
        **extra,
    }
