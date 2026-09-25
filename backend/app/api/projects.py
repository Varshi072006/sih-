from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.problems import serialize_problem, _get
from app.database.session import get_db
from app.models import (
    AuditLog,
    Industry,
    Problem,
    Project,
    ProjectMember,
    ProjectMilestone,
    University,
    User,
)
from app.schemas import MilestoneUpdateIn, ProjectCreateIn, TeamMemberIn
from app.security.deps import get_current_user, get_optional_user, require_roles
from app.services.audit import AuditLogService
from app.services.ids import next_project_public_id
from app.utils.constants import ADMIN_ROLES, GOVERNMENT_ROLES, MILESTONE_NAMES, UNIVERSITY_ROLES

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    items = db.query(Project).order_by(Project.id.desc()).all()
    return [_brief(p, db) for p in items]


@router.get("/{project_ref}")
def detail(project_ref: str, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    p = _proj(db, project_ref)
    problem = db.get(Problem, p.problem_id)
    uni = db.get(University, p.university_id) if p.university_id else None
    ind = db.get(Industry, p.industry_id) if p.industry_id else None
    return {
        **_brief(p, db),
        "objectives": p.objectives,
        "technology": p.technology,
        "budget": p.budget,
        "timeline": p.timeline,
        "final_outcome": p.final_outcome,
        "problem": serialize_problem(db, problem, user) if problem else None,
        "university": uni.name if uni else None,
        "industry": ind.company_name if ind else None,
        "members": [
            {"id": m.id, "name": m.name, "type": m.member_type, "department": m.department, "role": m.role, "responsibilities": m.responsibilities}
            for m in p.members
        ],
        "milestones": [
            {
                "id": m.id,
                "name": m.name,
                "sequence": m.sequence,
                "deadline": m.deadline,
                "description": m.description,
                "deliverable": m.deliverable,
                "status": m.status,
                "comments": m.comments,
                "approved": m.approved,
            }
            for m in sorted(p.milestones, key=lambda x: x.sequence)
        ],
    }


@router.post("")
def create_project(payload: ProjectCreateIn, user: User = Depends(require_roles(*GOVERNMENT_ROLES, *UNIVERSITY_ROLES, *ADMIN_ROLES)), db: Session = Depends(get_db)):
    problem = db.get(Problem, payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    proj = Project(
        public_id=next_project_public_id(db),
        problem_id=problem.id,
        university_id=payload.university_id,
        industry_id=payload.industry_id,
        department_id=problem.assigned_department_id,
        title=payload.title,
        objectives=payload.objectives,
        technology=payload.technology,
        budget=payload.budget,
        timeline=payload.timeline,
        status="active",
    )
    db.add(proj)
    db.flush()
    for i, name in enumerate(MILESTONE_NAMES, start=1):
        db.add(ProjectMilestone(project_id=proj.id, name=name, sequence=i, description=f"{name} milestone", status="pending"))
    AuditLogService.log(db, "CREATE", "project", proj.public_id, user, details=proj.title)
    db.commit()
    return {"id": proj.id, "public_id": proj.public_id}


@router.post("/{project_ref}/members")
def add_member(project_ref: str, payload: TeamMemberIn, user: User = Depends(require_roles(*UNIVERSITY_ROLES, *ADMIN_ROLES)), db: Session = Depends(get_db)):
    proj = _proj(db, project_ref)
    rec = ProjectMember(
        project_id=proj.id,
        name=payload.name,
        member_type=payload.member_type,
        department=payload.department,
        role=payload.role,
        responsibilities=payload.responsibilities,
    )
    db.add(rec)
    db.commit()
    return {"id": rec.id}


@router.patch("/{project_ref}/milestones/{milestone_id}")
def update_milestone(project_ref: str, milestone_id: int, payload: MilestoneUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    proj = _proj(db, project_ref)
    ms = db.get(ProjectMilestone, milestone_id)
    if not ms or ms.project_id != proj.id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for field in ["status", "comments", "deadline", "description", "deliverable", "approved"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(ms, field, val)
    db.commit()
    return {"id": ms.id, "status": ms.status}


@router.post("/{project_ref}/complete")
def complete(project_ref: str, outcome: str = "", user: User = Depends(require_roles(*GOVERNMENT_ROLES, *ADMIN_ROLES)), db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    proj = _proj(db, project_ref)
    pending = [m for m in proj.milestones if not m.approved]
    if pending:
        raise HTTPException(status_code=400, detail="All milestones must be approved before completion")
    proj.status = "completed"
    proj.completed_at = datetime.now(timezone.utc)
    proj.final_outcome = outcome
    AuditLogService.log(db, "COMPLETE", "project", proj.public_id, user, details=outcome)
    db.commit()
    return {"status": proj.status}


def _proj(db: Session, ref: str) -> Project:
    p = db.query(Project).filter(Project.public_id == ref).first()
    if not p and ref.isdigit():
        p = db.get(Project, int(ref))
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def _brief(p: Project, db: Session) -> dict:
    problem = db.get(Problem, p.problem_id)
    done = sum(1 for m in p.milestones if m.status == "completed" or m.approved)
    total = max(len(p.milestones), 1)
    return {
        "id": p.id,
        "public_id": p.public_id,
        "title": p.title,
        "status": p.status,
        "is_demo": p.is_demo,
        "problem_id": problem.public_id if problem else None,
        "progress": round(100 * done / total),
    }
