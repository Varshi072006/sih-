from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Problem, ProblemStatusHistory, User
from app.services.audit import AuditLogService
from app.utils.constants import ALLOWED_TRANSITIONS, STATUS_LABELS


def transition_status(
    db: Session,
    problem: Problem,
    new_status: str,
    actor: User | None,
    note: str = "",
    ip: str = "",
    ua: str = "",
) -> Problem:
    current = problem.status
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: {STATUS_LABELS.get(current, current)} → {STATUS_LABELS.get(new_status, new_status)}",
        )
    previous = problem.status
    problem.status = new_status
    db.add(
        ProblemStatusHistory(
            problem_id=problem.id,
            previous_status=previous,
            new_status=new_status,
            actor_id=actor.id if actor else None,
            note=note,
        )
    )
    AuditLogService.log(
        db,
        action="UPDATE_STATUS",
        entity_type="problem",
        entity_id=problem.public_id,
        user=actor,
        previous_status=previous,
        new_status=new_status,
        details=note,
        ip_address=ip,
        user_agent=ua,
    )
    db.flush()
    return problem
