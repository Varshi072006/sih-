from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.pipeline import analyze_problem, match_universities
from app.api.problems import _get
from app.database.session import get_db
from app.models import GovernmentSolution, GovernmentSolutionVersion, User
from app.security.deps import require_roles
from app.utils.constants import ADMIN_ROLES, GOVERNMENT_ROLES

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/analyze/{problem_ref}")
def analyze(problem_ref: str, user: User = Depends(require_roles(*GOVERNMENT_ROLES, *ADMIN_ROLES)), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    rec = analyze_problem(db, p)
    db.commit()
    return {
        "domain": rec.domain,
        "subdomain": rec.subdomain,
        "confidence": rec.classification_confidence,
        "priority_label": rec.priority_label,
        "suggested_department": rec.suggested_department,
        "disclaimer": "AI provides decision support only. Authorized humans retain final control.",
    }


@router.get("/recommendations/{problem_ref}")
def recommendations(problem_ref: str, user: User = Depends(require_roles(*GOVERNMENT_ROLES, *ADMIN_ROLES)), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    sol = db.query(GovernmentSolution).filter(GovernmentSolution.problem_id == p.id).first()
    text = ""
    if sol:
        latest = (
            db.query(GovernmentSolutionVersion)
            .filter(GovernmentSolutionVersion.solution_id == sol.id)
            .order_by(GovernmentSolutionVersion.version.desc())
            .first()
        )
        if latest:
            text = f"{latest.description} {latest.action_taken}"
    rows = match_universities(db, p, text)
    db.commit()
    return [
        {
            "university_id": r.university_id,
            "matching_score": r.matching_score,
            "reason": r.reason,
            "relevant_department": r.relevant_department,
            "selected": r.selected,
        }
        for r in rows
    ]
