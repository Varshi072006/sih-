from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import ImpactMetric, Industry, Problem, Project, University
from app.utils.constants import CATEGORIES, STATUS_LABELS

router = APIRouter(prefix="/api", tags=["Public & Analytics"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    problems = db.query(Problem).all()
    return {
        "problems_submitted": len(problems),
        "problems_verified": sum(1 for p in problems if p.status not in {"submitted", "pending_government_verification", "rejected"}),
        "universities_participating": db.query(University).filter(University.verification_status.in_(["verified", "activated"])).count(),
        "industry_partners": db.query(Industry).filter(Industry.verification_status.in_(["verified", "activated"])).count(),
        "active_projects": db.query(Project).filter(Project.status == "active").count(),
        "solutions_deployed": sum(1 for p in problems if p.status in {"done_solution", "industry_participation", "implementation_pilot", "completed"}),
        "people_impacted": sum(p.estimated_affected_population for p in problems if p.status == "completed"),
        "demo": True,
    }


@router.get("/lookups")
def lookups():
    from app.utils.constants import JHARKHAND_DISTRICTS, INDUSTRY_PARTICIPATION_TYPES, STATUS_LABELS

    return {
        "categories": CATEGORIES,
        "districts": JHARKHAND_DISTRICTS,
        "statuses": STATUS_LABELS,
        "participation_types": INDUSTRY_PARTICIPATION_TYPES,
    }


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    problems = db.query(Problem).all()
    by_status = {}
    by_category = {}
    by_district = {}
    for p in problems:
        by_status[p.status] = by_status.get(p.status, 0) + 1
        by_category[p.category] = by_category.get(p.category, 0) + 1
        by_district[p.district] = by_district.get(p.district, 0) + 1
    return {
        "status": [{"name": STATUS_LABELS.get(k, k), "value": v} for k, v in by_status.items()],
        "category": [{"name": k, "value": v} for k, v in by_category.items()],
        "district": [{"name": k, "value": v} for k, v in by_district.items()],
        "universities": db.query(University).count(),
        "industries": db.query(Industry).count(),
        "projects": db.query(Project).count(),
    }


@router.get("/impact")
def impact(db: Session = Depends(get_db)):
    metrics = db.query(ImpactMetric).all()
    problems = db.query(Problem).all()
    projects = db.query(Project).all()
    return {
        "problems_completed": sum(1 for p in problems if p.status == "completed"),
        "projects_completed": sum(1 for p in projects if p.status == "completed"),
        "solutions_deployed": sum(1 for p in problems if p.status in {"done_solution", "completed", "implementation_pilot"}),
        "people_benefited": sum(m.people_benefited for m in metrics) or sum(p.estimated_affected_population for p in problems if p.status == "completed"),
        "districts_covered": len({p.district for p in problems}),
        "universities_involved": db.query(University).count(),
        "industry_partners": db.query(Industry).count(),
        "patents": sum(m.patents for m in metrics),
        "publications": sum(m.publications for m in metrics),
        "startups_created": sum(m.startups_created for m in metrics),
        "technologies_transferred": sum(m.technologies_transferred for m in metrics),
        "stories": [
            {
                "id": m.id,
                "before": m.before_text,
                "solution": m.solution_text,
                "after": m.after_text,
                "people_benefited": m.people_benefited,
                "verified": m.verified,
                "is_demo": m.is_demo,
                "problem_id": m.problem_id,
            }
            for m in metrics
        ],
    }


@router.get("/map/problems")
def map_problems(db: Session = Depends(get_db)):
    items = db.query(Problem).filter(Problem.latitude.isnot(None)).all()
    return [
        {
            "public_id": p.public_id,
            "title": p.title,
            "district": p.district,
            "category": p.category,
            "status": p.status,
            "lat": round(p.latitude, 2) if p.latitude else None,
            "lng": round(p.longitude, 2) if p.longitude else None,
            "is_demo": p.is_demo,
        }
        for p in items
    ]
