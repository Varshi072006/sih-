from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.problems import serialize_problem, _get
from app.database.session import get_db
from app.models import Industry, IndustryParticipation, IndustryProposal, Problem, User
from app.schemas import ParticipateIn, ProposalIn
from app.security.deps import require_roles
from app.services.audit import AuditLogService
from app.services.notifications import NotificationService
from app.utils.constants import ADMIN_ROLES, INDUSTRY_ROLES, INDUSTRY_PARTICIPATION_TYPES

router = APIRouter(prefix="/api/industry", tags=["Industry"])


def _org_user(user: User = Depends(require_roles(*INDUSTRY_ROLES, *ADMIN_ROLES))) -> User:
    if user.primary_role in ADMIN_ROLES:
        return user
    if user.verification_status not in {"verified", "activated"}:
        raise HTTPException(status_code=403, detail="Industry account pending verification")
    return user


@router.get("")
def public_list(sector: str | None = None, district: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Industry).filter(Industry.verification_status.in_(["verified", "activated"]))
    if sector:
        query = query.filter(Industry.sector.ilike(f"%{sector}%"))
    if district:
        query = query.filter(Industry.district == district)
    if q:
        query = query.filter(Industry.company_name.ilike(f"%{q}%"))
    return [
        {
            "id": i.id,
            "company_name": i.company_name,
            "organization_type": i.organization_type,
            "sector": i.sector,
            "district": i.district,
            "technologies": i.technologies,
            "csr_areas": i.csr_areas,
            "is_demo": i.is_demo,
            "capabilities": [c.name for c in i.capabilities if c.enabled],
        }
        for i in query.all()
    ]


@router.get("/me")
def me(user: User = Depends(_org_user)):
    org = user.industry
    if not org:
        raise HTTPException(status_code=404, detail="Industry profile not found")
    return {
        "id": org.id,
        "company_name": org.company_name,
        "organization_type": org.organization_type,
        "sector": org.sector,
        "district": org.district,
        "technologies": org.technologies,
        "verification_status": org.verification_status,
        "is_demo": org.is_demo,
        "capabilities": [c.name for c in org.capabilities if c.enabled],
    }


@router.get("/problems")
def available(user: User = Depends(_org_user), db: Session = Depends(get_db)):
    items = db.query(Problem).filter(Problem.status.in_(["done_solution", "industry_participation", "implementation_pilot"])).all()
    return [serialize_problem(db, p, user) for p in items]


@router.get("/problems/{problem_ref}")
def detail(problem_ref: str, user: User = Depends(_org_user), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    if p.status not in {"done_solution", "industry_participation", "implementation_pilot", "completed"}:
        raise HTTPException(status_code=403, detail="This problem is not yet available for industry participation")
    return serialize_problem(db, p, user, detail=True)


@router.post("/problems/{problem_ref}/participate")
def participate(problem_ref: str, payload: ParticipateIn, user: User = Depends(_org_user), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    org = user.industry
    if p.status not in {"done_solution", "industry_participation", "implementation_pilot"}:
        raise HTTPException(status_code=400, detail="Industry participation is only available after Done Solution")
    types = [t for t in payload.participation_types if t in INDUSTRY_PARTICIPATION_TYPES]
    if not types:
        raise HTTPException(status_code=400, detail="Select at least one valid participation type")
    rec = IndustryParticipation(
        problem_id=p.id,
        industry_id=org.id,
        participation_types=",".join(types),
        status="expressed_interest",
    )
    db.add(rec)
    if p.status == "done_solution":
        from app.services.workflow import transition_status

        try:
            transition_status(db, p, "industry_participation", user, f"{org.company_name} expressed interest")
        except Exception:
            pass
    NotificationService.notify_role(
        db,
        "government_officer",
        "industry",
        "Industry expressed interest",
        f"{org.company_name} wants to participate in {p.public_id}",
        "problem",
        p.public_id,
    )
    AuditLogService.log(db, "PARTICIPATE", "industry_participation", p.public_id, user, details=",".join(types))
    db.commit()
    return {"id": rec.id, "status": rec.status, "message": "Participation recorded. This does not block government workflow."}


@router.post("/problems/{problem_ref}/proposal")
def proposal(problem_ref: str, payload: ProposalIn, user: User = Depends(_org_user), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    org = user.industry
    part = (
        db.query(IndustryParticipation)
        .filter(IndustryParticipation.problem_id == p.id, IndustryParticipation.industry_id == org.id)
        .order_by(IndustryParticipation.id.desc())
        .first()
    )
    if not part:
        part = IndustryParticipation(problem_id=p.id, industry_id=org.id, participation_types="Proposal", status="proposal_submitted")
        db.add(part)
        db.flush()
    rec = IndustryProposal(
        participation_id=part.id,
        problem_id=p.id,
        industry_id=org.id,
        proposal=payload.proposal,
        technology_offered=payload.technology_offered,
        resources=payload.resources,
        estimated_budget=payload.estimated_budget,
        timeline=payload.timeline,
        team=payload.team,
        expected_contribution=payload.expected_contribution,
    )
    db.add(rec)
    NotificationService.notify_role(db, "government_officer", "industry", "Industry proposal received", f"{org.company_name} proposed support for {p.public_id}", "problem", p.public_id)
    NotificationService.notify_role(db, "admin", "industry", "Industry proposal", f"{org.company_name} / {p.public_id}", "problem", p.public_id)
    AuditLogService.log(db, "CREATE", "industry_proposal", p.public_id, user)
    db.commit()
    return {"id": rec.id, "review_status": rec.review_status}


@router.get("/collaborations")
def collaborations(user: User = Depends(_org_user), db: Session = Depends(get_db)):
    org = user.industry
    parts = db.query(IndustryParticipation).filter(IndustryParticipation.industry_id == org.id).all()
    out = []
    for p in parts:
        problem = db.get(Problem, p.problem_id)
        out.append(
            {
                "id": p.id,
                "problem_id": problem.public_id if problem else p.problem_id,
                "title": problem.title if problem else "",
                "types": p.participation_types,
                "status": p.status,
            }
        )
    return out
