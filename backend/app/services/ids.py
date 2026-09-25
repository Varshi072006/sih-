from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Problem


def next_problem_public_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"JH-PR-{year}-"
    last = (
        db.query(Problem)
        .filter(Problem.public_id.like(f"{prefix}%"))
        .order_by(Problem.id.desc())
        .first()
    )
    n = 1
    if last:
        try:
            n = int(last.public_id.split("-")[-1]) + 1
        except ValueError:
            n = 1
    return f"{prefix}{n:05d}"


def next_project_public_id(db: Session) -> str:
    from app.models import Project

    year = datetime.now(timezone.utc).year
    prefix = f"JH-PJ-{year}-"
    last = (
        db.query(Project)
        .filter(Project.public_id.like(f"{prefix}%"))
        .order_by(Project.id.desc())
        .first()
    )
    n = 1
    if last:
        try:
            n = int(last.public_id.split("-")[-1]) + 1
        except ValueError:
            n = 1
    return f"{prefix}{n:05d}"
