import json

from sqlalchemy.orm import Session

from app.ai.classification_service import classification_service
from app.ai.duplicate_detection_service import duplicate_detection_service
from app.ai.priority_service import priority_service
from app.ai.university_matching_service import university_matching_service
from app.models import (
    AIAnalysis,
    AIDuplicateMatch,
    AIUniversityRecommendation,
    Problem,
    University,
    UniversityDepartment,
)


def analyze_problem(db: Session, problem: Problem) -> AIAnalysis:
    classification = classification_service.classify(problem.title, problem.description, problem.category)
    others = (
        db.query(Problem)
        .filter(Problem.id != problem.id, Problem.status != "rejected")
        .limit(80)
        .all()
    )
    corpus = [
        {
            "id": p.id,
            "public_id": p.public_id,
            "title": p.title,
            "text": f"{p.title} {p.description} {p.district}",
        }
        for p in others
    ]
    dupes = duplicate_detection_service.find_related(f"{problem.title} {problem.description}", corpus)
    db.query(AIDuplicateMatch).filter(AIDuplicateMatch.problem_id == problem.id).delete()
    for d in dupes:
        db.add(
            AIDuplicateMatch(
                problem_id=problem.id,
                matched_problem_id=d["problem_id"],
                similarity=d["similarity"],
                reason=d["reason"],
            )
        )
    evidence_count = len(problem.evidence or [])
    priority = priority_service.recommend(
        problem.estimated_affected_population,
        problem.urgency,
        problem.severity,
        evidence_count,
        problem.geographic_impact,
        len(dupes),
    )
    rec = (
        db.query(AIAnalysis).filter(AIAnalysis.problem_id == problem.id).order_by(AIAnalysis.id.desc()).first()
    )
    if not rec:
        rec = AIAnalysis(problem_id=problem.id)
        db.add(rec)
    rec.domain = classification["domain"]
    rec.subdomain = classification["subdomain"]
    rec.keywords = ",".join(classification["keywords"])
    rec.suggested_department = classification["suggested_department"]
    rec.classification_confidence = classification["confidence"]
    rec.priority_score = priority["priority_score"]
    rec.priority_label = priority["priority_label"]
    rec.priority_factors = json.dumps(priority["factors"])
    rec.model_used = classification["model_used"]
    rec.explanation = f"{classification['reason']} {priority['reason']}"
    db.flush()
    return rec


def match_universities(db: Session, problem: Problem, solution_text: str = "") -> list[AIUniversityRecommendation]:
    unis = db.query(University).filter(University.verification_status.in_(["verified", "activated"])).all()
    payload = []
    for u in unis:
        depts = ", ".join(d.name for d in u.departments)
        payload.append(
            {
                "id": u.id,
                "name": u.name,
                "departments": depts,
                "faculty_expertise": u.faculty_expertise,
                "research_areas": u.research_areas,
                "laboratories": u.laboratories,
                "previous_projects": u.previous_projects,
                "technologies": u.technologies,
            }
        )
    text = f"{problem.title} {problem.description} {problem.category} {problem.district} {solution_text}"
    matches = university_matching_service.match(text, payload)
    db.query(AIUniversityRecommendation).filter(AIUniversityRecommendation.problem_id == problem.id).delete()
    rows = []
    for m in matches:
        row = AIUniversityRecommendation(
            problem_id=problem.id,
            university_id=m["university_id"],
            matching_score=m["matching_score"],
            reason=m["reason"],
            relevant_department=m["relevant_department"],
            relevant_expertise=m["relevant_expertise"],
            relevant_laboratory=m["relevant_laboratory"],
            relevant_previous_project=m["relevant_previous_project"],
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows
