from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.ai.pipeline import analyze_problem
from app.database.session import get_db
from app.models import (
    AIAnalysis,
    AIDuplicateMatch,
    AIUniversityRecommendation,
    CitizenFeedback,
    GovernmentSolution,
    GovernmentSolutionVersion,
    IndustryParticipation,
    IndustryProposal,
    Problem,
    ProblemEvidence,
    ProblemLocation,
    ProblemRelation,
    ProblemStatusHistory,
    University,
    UniversityOpinion,
    UniversityReview,
    User,
)
from app.schemas import FeedbackIn, ProblemCreateIn
from app.security.deps import get_current_user, get_optional_user, is_gov, is_university, is_industry
from app.services.ids import next_problem_public_id
from app.services.audit import AuditLogService
from app.services.notifications import NotificationService
from app.services.storage import save_upload
from app.services.workflow import transition_status
from app.utils.constants import ADMIN_ROLES, CATEGORIES, STATUS_LABELS

router = APIRouter(prefix="/api/problems", tags=["Problems"])


def serialize_problem(db: Session, p: Problem, viewer: User | None, detail: bool = False) -> dict:
    data = {
        "id": p.id,
        "public_id": p.public_id,
        "title": p.title,
        "description": p.description if detail else (p.description[:240] + ("…" if len(p.description) > 240 else "")),
        "category": p.category,
        "subcategory": p.subcategory,
        "district": p.district,
        "block": p.block,
        "village": p.village,
        "status": p.status,
        "status_label": STATUS_LABELS.get(p.status, p.status),
        "severity": p.severity,
        "urgency": p.urgency,
        "estimated_affected_population": p.estimated_affected_population,
        "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
        "is_demo": p.is_demo,
        "assigned_department": p.assigned_department.name if p.assigned_department else None,
        "latitude": p.latitude if (viewer and (is_gov(viewer) or viewer.id == p.citizen_id or viewer.primary_role in ADMIN_ROLES)) else (round(p.latitude, 2) if p.latitude else None),
        "longitude": p.longitude if (viewer and (is_gov(viewer) or viewer.id == p.citizen_id or viewer.primary_role in ADMIN_ROLES)) else (round(p.longitude, 2) if p.longitude else None),
    }
    if not detail:
        return data
    data.update(
        {
            "expected_solution": p.expected_solution,
            "affected_people_description": p.affected_people_description,
            "address": p.address if viewer and (is_gov(viewer) or viewer.id == p.citizen_id or viewer.primary_role in ADMIN_ROLES) else "",
            "frequency": p.frequency,
            "geographic_impact": p.geographic_impact,
            "existing_solution": p.existing_solution,
            "current_government_action": p.current_government_action,
            "official_remarks": p.official_remarks if viewer and is_gov(viewer) else "",
            "citizen_name": p.citizen.full_name if viewer and is_gov(viewer) else None,
        }
    )
    data["evidence"] = [
        {
            "id": e.id,
            "type": e.evidence_type,
            "file_id": e.stored_file_id,
            "gps_from_image": e.gps_from_image,
            "latitude": e.latitude,
            "longitude": e.longitude,
        }
        for e in p.evidence
    ]
    data["timeline"] = [
        {
            "id": h.id,
            "previous_status": STATUS_LABELS.get(h.previous_status, h.previous_status),
            "new_status": STATUS_LABELS.get(h.new_status, h.new_status),
            "note": h.note,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in sorted(p.status_history, key=lambda x: x.id)
    ]
    sol = db.query(GovernmentSolution).filter(GovernmentSolution.problem_id == p.id).first()
    if sol:
        versions = (
            db.query(GovernmentSolutionVersion)
            .filter(GovernmentSolutionVersion.solution_id == sol.id)
            .order_by(GovernmentSolutionVersion.version)
            .all()
        )
        data["solutions"] = [
            {
                "version": v.version,
                "description": v.description,
                "action_taken": v.action_taken,
                "implementation_details": v.implementation_details,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]
        data["solution_done"] = sol.is_done
    else:
        data["solutions"] = []
        data["solution_done"] = False

    show_ai = viewer and (is_gov(viewer) or viewer.primary_role in ADMIN_ROLES)
    if show_ai:
        analysis = db.query(AIAnalysis).filter(AIAnalysis.problem_id == p.id).order_by(AIAnalysis.id.desc()).first()
        if analysis:
            data["ai"] = {
                "domain": analysis.domain,
                "subdomain": analysis.subdomain,
                "keywords": analysis.keywords.split(",") if analysis.keywords else [],
                "suggested_department": analysis.suggested_department,
                "confidence": analysis.classification_confidence,
                "priority_score": analysis.priority_score,
                "priority_label": analysis.priority_label,
                "priority_factors": analysis.priority_factors,
                "explanation": analysis.explanation,
                "model_used": analysis.model_used,
            }
        dupes = db.query(AIDuplicateMatch).filter(AIDuplicateMatch.problem_id == p.id).all()
        data["duplicates"] = []
        for d in dupes:
            other = db.get(Problem, d.matched_problem_id)
            data["duplicates"].append(
                {
                    "id": d.id,
                    "problem_id": other.public_id if other else d.matched_problem_id,
                    "internal_id": d.matched_problem_id,
                    "title": other.title if other else "",
                    "similarity": d.similarity,
                    "reason": d.reason,
                    "decision": d.human_decision,
                }
            )
        recs = db.query(AIUniversityRecommendation).filter(AIUniversityRecommendation.problem_id == p.id).all()
        data["university_recommendations"] = []
        for r in recs:
            uni = db.get(University, r.university_id)
            data["university_recommendations"].append(
                {
                    "id": r.id,
                    "university_id": r.university_id,
                    "university": uni.name if uni else "",
                    "matching_score": r.matching_score,
                    "reason": r.reason,
                    "relevant_department": r.relevant_department,
                    "relevant_expertise": r.relevant_expertise,
                    "relevant_laboratory": r.relevant_laboratory,
                    "relevant_previous_project": r.relevant_previous_project,
                    "selected": r.selected,
                }
            )
    opinions = db.query(UniversityOpinion).filter(UniversityOpinion.problem_id == p.id).all()
    if viewer and (is_gov(viewer) or is_university(viewer) or viewer.primary_role in ADMIN_ROLES):
        data["opinions"] = []
        for o in opinions:
            uni = db.get(University, o.university_id)
            data["opinions"].append(
                {
                    "id": o.id,
                    "university": uni.name if uni else "",
                    "suggestion": o.suggestion,
                    "recommended_improvement": o.recommended_improvement,
                    "technical_recommendation": o.technical_recommendation,
                    "alternative_solution": o.alternative_solution,
                    "expected_benefit": o.expected_benefit,
                    "government_decision": o.government_decision,
                    "government_remarks": o.government_remarks if is_gov(viewer) else "",
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
            )
        reviews = db.query(UniversityReview).filter(UniversityReview.problem_id == p.id).all()
        data["reviews"] = [
            {"decision": r.decision, "note": r.note, "university_id": r.university_id, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in reviews
        ]
    if viewer and (is_gov(viewer) or is_industry(viewer) or viewer.primary_role in ADMIN_ROLES) and p.status in {
        "done_solution",
        "industry_participation",
        "implementation_pilot",
        "completed",
    }:
        parts = db.query(IndustryParticipation).filter(IndustryParticipation.problem_id == p.id).all()
        data["participations"] = []
        for part in parts:
            props = db.query(IndustryProposal).filter(IndustryProposal.participation_id == part.id).all()
            data["participations"].append(
                {
                    "id": part.id,
                    "industry_id": part.industry_id,
                    "types": part.participation_types,
                    "status": part.status,
                    "proposals": [
                        {
                            "id": pr.id,
                            "proposal": pr.proposal,
                            "technology_offered": pr.technology_offered,
                            "review_status": pr.review_status,
                        }
                        for pr in props
                    ],
                }
            )
    if viewer and (viewer.id == p.citizen_id or is_gov(viewer)):
        data["feedback"] = [
            {"satisfaction": f.satisfaction, "resolved": f.resolved, "comments": f.comments}
            for f in db.query(CitizenFeedback).filter(CitizenFeedback.problem_id == p.id).all()
        ]
    else:
        data["feedback"] = []
    return data


@router.get("")
def list_problems(
    status: str | None = None,
    district: str | None = None,
    category: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    query = db.query(Problem)
    if status:
        query = query.filter(Problem.status == status)
    if district:
        query = query.filter(Problem.district == district)
    if category:
        query = query.filter(Problem.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter((Problem.title.ilike(like)) | (Problem.public_id.ilike(like)))
    items = query.order_by(Problem.id.desc()).limit(200).all()
    return [serialize_problem(db, p, viewer) for p in items]


@router.get("/mine")
def my_problems(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Problem).filter(Problem.citizen_id == user.id).order_by(Problem.id.desc()).all()
    return [serialize_problem(db, p, user) for p in items]


@router.get("/{problem_ref}")
def get_problem(problem_ref: str, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    p = _get(db, problem_ref)
    return serialize_problem(db, p, viewer, detail=True)


@router.post("")
def create_problem(payload: ProblemCreateIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.primary_role != "citizen" and user.primary_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only citizens can submit problems")
    if payload.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    if payload.latitude is None or payload.longitude is None:
        raise HTTPException(status_code=400, detail="Map location (latitude and longitude) is required")
    problem = Problem(
        public_id=next_problem_public_id(db),
        citizen_id=user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        subcategory=payload.subcategory,
        expected_solution=payload.expected_solution,
        affected_people_description=payload.affected_people_description,
        district=payload.district,
        block=payload.block,
        village=payload.village,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        estimated_affected_population=payload.estimated_affected_population,
        severity=payload.severity,
        urgency=payload.urgency,
        frequency=payload.frequency,
        geographic_impact=payload.geographic_impact,
        existing_solution=payload.existing_solution,
        current_government_action=payload.current_government_action,
        status="submitted",
    )
    db.add(problem)
    db.flush()
    db.add(
        ProblemLocation(
            problem_id=problem.id,
            district=payload.district,
            block=payload.block,
            village=payload.village,
            address=payload.address,
            latitude=payload.latitude,
            longitude=payload.longitude,
            source=payload.location_source,
        )
    )
    transition_status(db, problem, "pending_government_verification", user, "Problem submitted")
    AuditLogService.log(db, "CREATE", "problem", problem.public_id, user, new_status=problem.status, details=problem.title)
    NotificationService.notify_user(
        db, user.id, "problem", "Problem submitted", f"{problem.public_id} is pending government verification.", "problem", problem.public_id
    )
    NotificationService.notify_role(
        db, "government_officer", "problem", "New problem submitted", f"{problem.public_id}: {problem.title}", "problem", problem.public_id
    )
    NotificationService.notify_role(
        db, "admin", "problem", "New problem", f"{problem.public_id}: {problem.title}", "problem", problem.public_id
    )
    db.commit()
    db.refresh(problem)
    return {
        "message": "Problem successfully submitted",
        "public_id": problem.public_id,
        "status": problem.status,
        "status_label": STATUS_LABELS[problem.status],
        "submitted_at": problem.submitted_at.isoformat(),
        "id": problem.id,
    }


@router.post("/{problem_ref}/evidence")
def upload_evidence(
    problem_ref: str,
    evidence_type: str = Form(...),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    gps_from_image: bool = Form(False),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = _get(db, problem_ref)
    if p.citizen_id != user.id and user.primary_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Not allowed")
    stored = save_upload(db, file, user.id, "problem_evidence", str(p.id), public=False)
    rec = ProblemEvidence(
        problem_id=p.id,
        stored_file_id=stored.id,
        evidence_type=evidence_type,
        latitude=latitude,
        longitude=longitude,
        gps_from_image=bool(gps_from_image),
    )
    db.add(rec)
    if evidence_type == "gps_location":
        analyze_problem(db, p)
        NotificationService.notify_role(db, "admin", "ai", "AI analysis completed", f"Analysis ready for {p.public_id}", "problem", p.public_id)
    db.commit()
    return {"id": rec.id, "file_id": stored.id}


@router.post("/{problem_ref}/feedback")
def feedback(problem_ref: str, payload: FeedbackIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    if p.citizen_id != user.id:
        raise HTTPException(status_code=403, detail="Only the submitting citizen can provide feedback")
    if p.status not in {"implementation_pilot", "completed", "done_solution", "industry_participation"}:
        raise HTTPException(status_code=400, detail="Feedback is available after implementation")
    rec = CitizenFeedback(
        problem_id=p.id,
        citizen_id=user.id,
        satisfaction=payload.satisfaction,
        resolved=payload.resolved,
        comments=payload.comments,
    )
    db.add(rec)
    AuditLogService.log(db, "CREATE", "feedback", p.public_id, user, details=payload.comments)
    db.commit()
    return {"message": "Feedback recorded"}


def _get(db: Session, ref: str) -> Problem:
    q = db.query(Problem)
    p = q.filter(Problem.public_id == ref).first()
    if not p and ref.isdigit():
        p = db.get(Problem, int(ref))
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
    return p
