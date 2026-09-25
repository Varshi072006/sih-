from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.problems import serialize_problem
from app.database.session import get_db
from app.models import (
    AIAnalysis,
    AIDuplicateMatch,
    AIUniversityRecommendation,
    AuditLog,
    Industry,
    Problem,
    Project,
    University,
    User,
)
from app.schemas import RemarksIn
from app.security.deps import require_roles
from app.services.audit import AuditLogService
from app.services.notifications import NotificationService
from app.utils.constants import ADMIN_ROLES

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _admin(user: User = Depends(require_roles(*ADMIN_ROLES))) -> User:
    return user


@router.get("/dashboard")
def dashboard(user: User = Depends(_admin), db: Session = Depends(get_db)):
    return {
        "total_users": db.query(User).count(),
        "pending_registrations": db.query(User).filter(User.verification_status == "pending_verification").count(),
        "total_problems": db.query(Problem).count(),
        "pending_verification": db.query(Problem).filter(Problem.status == "pending_government_verification").count(),
        "verified_problems": db.query(Problem).filter(Problem.status.in_(["verified", "assigned_to_department", "under_department_review"])).count(),
        "university_reviews": db.query(Problem).filter(Problem.status.in_(["university_review", "university_opinion_submitted"])).count(),
        "industry_participation": db.query(Problem).filter(Problem.status.in_(["done_solution", "industry_participation"])).count(),
        "active_projects": db.query(Project).filter(Project.status == "active").count(),
        "completed_problems": db.query(Problem).filter(Problem.status == "completed").count(),
        "people_impacted": sum(p.estimated_affected_population for p in db.query(Problem).filter(Problem.status == "completed").all()),
    }


@router.get("/users")
def users(role: str | None = None, status: str | None = None, user: User = Depends(_admin), db: Session = Depends(get_db)):
    q = db.query(User)
    if role:
        q = q.filter(User.primary_role == role)
    if status:
        q = q.filter(User.verification_status == status)
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "primary_role": u.primary_role,
            "verification_status": u.verification_status,
            "is_active": u.is_active,
            "is_demo": u.is_demo,
            "mobile": u.mobile,
        }
        for u in q.order_by(User.id.desc()).all()
    ]


@router.post("/users/{user_id}/{action}")
def user_action(user_id: int, action: str, payload: RemarksIn | None = None, admin: User = Depends(_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    remarks = payload.remarks if payload else ""
    if action in {"verify", "approve"}:
        target.verification_status = "verified"
        if target.university:
            target.university.verification_status = "verified"
        if target.industry:
            target.industry.verification_status = "verified"
        NotificationService.notify_user(db, target.id, "account", "Account approved", "Your account has been verified and activated.", "user", str(target.id))
    elif action == "reject":
        target.verification_status = "rejected"
        NotificationService.notify_user(db, target.id, "account", "Registration rejected", remarks or "Your registration was not approved.", "user", str(target.id))
    elif action == "suspend":
        target.is_active = False
        target.verification_status = "suspended"
    elif action == "reactivate":
        target.is_active = True
        target.verification_status = "verified"
    elif action == "more-info":
        target.verification_status = "more_information_required"
        NotificationService.notify_user(db, target.id, "account", "More information required", remarks, "user", str(target.id))
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    AuditLogService.log(db, action.upper(), "user", str(target.id), admin, details=remarks)
    db.commit()
    return {"id": target.id, "verification_status": target.verification_status, "is_active": target.is_active}


@router.get("/universities")
def universities(admin: User = Depends(_admin), db: Session = Depends(get_db)):
    return [
        {
            "id": u.id,
            "name": u.name,
            "district": u.district,
            "user_id": u.user_id,
            "departments": [d.name for d in u.departments],
            "expertise": u.faculty_expertise,
            "research_areas": u.research_areas,
            "laboratories": u.laboratories,
            "verification_status": u.verification_status,
            "is_demo": u.is_demo,
        }
        for u in db.query(University).all()
    ]


@router.get("/industries")
def industries(admin: User = Depends(_admin), db: Session = Depends(get_db)):
    return [
        {
            "id": i.id,
            "company_name": i.company_name,
            "organization_type": i.organization_type,
            "sector": i.sector,
            "technologies": i.technologies,
            "csr_areas": i.csr_areas,
            "user_id": i.user_id,
            "verification_status": i.verification_status,
            "is_demo": i.is_demo,
            "capabilities": [c.name for c in i.capabilities if c.enabled],
        }
        for i in db.query(Industry).all()
    ]


@router.get("/problems")
def problems(admin: User = Depends(_admin), db: Session = Depends(get_db)):
    return [serialize_problem(db, p, admin) for p in db.query(Problem).order_by(Problem.id.desc()).all()]


@router.get("/projects")
def projects(admin: User = Depends(_admin), db: Session = Depends(get_db)):
    return [
        {"id": p.id, "public_id": p.public_id, "title": p.title, "status": p.status, "is_demo": p.is_demo}
        for p in db.query(Project).all()
    ]


@router.get("/ai")
def ai_monitor(admin: User = Depends(_admin), db: Session = Depends(get_db)):
    analyses = db.query(AIAnalysis).order_by(AIAnalysis.id.desc()).limit(100).all()
    out = []
    for a in analyses:
        p = db.get(Problem, a.problem_id)
        dupes = db.query(AIDuplicateMatch).filter(AIDuplicateMatch.problem_id == a.problem_id).all()
        recs = db.query(AIUniversityRecommendation).filter(AIUniversityRecommendation.problem_id == a.problem_id).all()
        out.append(
            {
                "problem_id": p.public_id if p else a.problem_id,
                "domain": a.domain,
                "subdomain": a.subdomain,
                "confidence": a.classification_confidence,
                "priority_label": a.priority_label,
                "priority_score": a.priority_score,
                "suggested_department": a.suggested_department,
                "model_used": a.model_used,
                "duplicates": [{"similarity": d.similarity, "reason": d.reason} for d in dupes],
                "universities": [{"score": r.matching_score, "reason": r.reason, "university_id": r.university_id, "selected": r.selected} for r in recs],
            }
        )
    return out


@router.get("/audit-logs")
def audit_logs(admin: User = Depends(_admin), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(300).all()
    return [
        {
            "id": l.id,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "user_id": l.user_id,
            "role": l.role,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "previous_status": l.previous_status,
            "new_status": l.new_status,
            "details": l.details,
            "ip_address": l.ip_address,
        }
        for l in logs
    ]
