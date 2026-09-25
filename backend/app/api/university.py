from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.problems import serialize_problem, _get
from app.database.session import get_db
from app.models import (
    AIUniversityRecommendation,
    Problem,
    University,
    UniversityOpinion,
    UniversityOpinionAttachment,
    UniversityReview,
    User,
)
from app.schemas import OpinionIn, RemarksIn, TeamMemberIn
from app.security.deps import get_current_user, require_roles
from app.services.audit import AuditLogService
from app.services.notifications import NotificationService
from app.services.storage import save_upload
from app.services.workflow import transition_status
from app.utils.constants import ADMIN_ROLES, UNIVERSITY_ROLES

router = APIRouter(prefix="/api/universities", tags=["Universities"])


def _uni_user(user: User = Depends(require_roles(*UNIVERSITY_ROLES, *ADMIN_ROLES))) -> User:
    if user.primary_role in ADMIN_ROLES:
        return user
    if user.verification_status not in {"verified", "activated"}:
        raise HTTPException(status_code=403, detail="University account pending verification")
    return user


@router.get("")
def public_list(district: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(University).filter(University.verification_status.in_(["verified", "activated"]))
    if district:
        query = query.filter(University.district == district)
    if q:
        like = f"%{q}%"
        query = query.filter((University.name.ilike(like)) | (University.research_areas.ilike(like)))
    items = query.all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "district": u.district,
            "institution_type": u.institution_type,
            "research_areas": u.research_areas,
            "laboratories": u.laboratories,
            "technologies": u.technologies,
            "is_demo": u.is_demo,
            "departments": [d.name for d in u.departments],
        }
        for u in items
    ]


@router.get("/me")
def me(user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    uni = user.university
    if not uni and user.primary_role in ADMIN_ROLES:
        uni = db.query(University).first()
    if not uni:
        raise HTTPException(status_code=404, detail="University profile not found")
    return {
        "id": uni.id,
        "name": uni.name,
        "district": uni.district,
        "departments": [d.name for d in uni.departments],
        "faculty_expertise": uni.faculty_expertise,
        "research_areas": uni.research_areas,
        "laboratories": uni.laboratories,
        "verification_status": uni.verification_status,
        "is_demo": uni.is_demo,
        "faculty": [{"id": f.id, "name": f.name, "department": f.department, "expertise": f.expertise} for f in uni.faculty],
        "students": [{"id": s.id, "name": s.name, "department": s.department} for s in uni.students],
    }


@router.get("/problems")
def problems(user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    uni = user.university
    if not uni:
        raise HTTPException(status_code=404, detail="University profile not found")
    rec_ids = [
        r.problem_id
        for r in db.query(AIUniversityRecommendation).filter(
            AIUniversityRecommendation.university_id == uni.id,
            AIUniversityRecommendation.selected.is_(True),
        ).all()
    ]
    recommended = db.query(Problem).filter(Problem.id.in_(rec_ids)).all() if rec_ids else []
    available = db.query(Problem).filter(Problem.status.in_(["university_review", "universities_notified", "university_opinion_submitted"])).all()
    return {
        "recommended": [serialize_problem(db, p, user) for p in recommended],
        "available": [serialize_problem(db, p, user) for p in available],
        "for_review": [serialize_problem(db, p, user) for p in recommended or available],
    }


@router.get("/problems/{problem_ref}")
def problem_detail(problem_ref: str, user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    return serialize_problem(db, _get(db, problem_ref), user, detail=True)


@router.post("/problems/{problem_ref}/review")
def review(problem_ref: str, payload: RemarksIn, user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    uni = user.university
    db.add(UniversityReview(problem_id=p.id, university_id=uni.id, reviewer_id=user.id, decision="review", note=payload.remarks))
    AuditLogService.log(db, "UPDATE", "university_review", p.public_id, user, details="review")
    db.commit()
    return {"message": "Review recorded"}


@router.post("/problems/{problem_ref}/clarification")
def clarification(problem_ref: str, payload: RemarksIn, user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    uni = user.university
    db.add(UniversityReview(problem_id=p.id, university_id=uni.id, reviewer_id=user.id, decision="clarification", note=payload.remarks))
    NotificationService.notify_role(
        db,
        "government_officer",
        "problem",
        "Clarification requested",
        f"{uni.name} requested clarification on {p.public_id}: {payload.remarks}",
        "problem",
        p.public_id,
    )
    db.commit()
    return {"message": "Clarification requested"}


@router.post("/problems/{problem_ref}/no-opinion")
def no_opinion(problem_ref: str, user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    uni = user.university
    db.add(UniversityReview(problem_id=p.id, university_id=uni.id, reviewer_id=user.id, decision="no_opinion", note=""))
    if p.status == "university_review":
        try:
            transition_status(db, p, "no_opinion", user, f"{uni.name} recorded no opinion")
        except Exception:
            pass
    NotificationService.notify_role(
        db,
        "government_officer",
        "problem",
        "University recorded no opinion",
        f"{uni.name} recorded no opinion on {p.public_id}.",
        "problem",
        p.public_id,
    )
    AuditLogService.log(db, "UPDATE", "university_review", p.public_id, user, details="no_opinion")
    db.commit()
    return {"message": "No opinion recorded", "status": p.status}


@router.post("/problems/{problem_ref}/opinion")
def opinion(
    problem_ref: str,
    payload: OpinionIn,
    user: User = Depends(_uni_user),
    db: Session = Depends(get_db),
):
    p = _get(db, problem_ref)
    uni = user.university
    rec = UniversityOpinion(
        problem_id=p.id,
        university_id=uni.id,
        author_id=user.id,
        suggestion=payload.suggestion,
        recommended_improvement=payload.recommended_improvement,
        technical_recommendation=payload.technical_recommendation,
        alternative_solution=payload.alternative_solution,
        expected_benefit=payload.expected_benefit,
    )
    db.add(rec)
    db.flush()
    db.add(UniversityReview(problem_id=p.id, university_id=uni.id, reviewer_id=user.id, decision="suggestion", note="opinion submitted"))
    if p.status in {"university_review", "universities_notified"}:
        try:
            if p.status == "universities_notified":
                transition_status(db, p, "university_review", user, "Review started")
            transition_status(db, p, "university_opinion_submitted", user, f"{uni.name} submitted opinion")
        except Exception:
            p.status = "university_opinion_submitted"
    NotificationService.notify_role(
        db,
        "government_officer",
        "problem",
        "University opinion submitted",
        f"{uni.name} has submitted an opinion regarding Problem {p.public_id}.",
        "problem",
        p.public_id,
    )
    if p.assigned_department_id:
        NotificationService.notify_department(
            db,
            p.assigned_department_id,
            notification_type="problem",
            title="University opinion submitted",
            message=f"{uni.name} has submitted an opinion regarding Problem {p.public_id}.",
            entity_type="problem",
            entity_id=p.public_id,
        )
    AuditLogService.log(db, "SUBMIT_OPINION", "university_opinion", str(rec.id), user, details=p.public_id)
    db.commit()
    return {"id": rec.id, "status": p.status}


@router.post("/opinions/{opinion_id}/attachments")
def attach(opinion_id: int, file: UploadFile, user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    op = db.get(UniversityOpinion, opinion_id)
    if not op:
        raise HTTPException(status_code=404, detail="Opinion not found")
    stored = save_upload(db, file, user.id, "university_opinion", str(opinion_id))
    db.add(UniversityOpinionAttachment(opinion_id=op.id, stored_file_id=stored.id))
    db.commit()
    return {"file_id": stored.id}


@router.post("/faculty")
def add_faculty(payload: TeamMemberIn, user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    from app.models import Faculty

    uni = user.university
    rec = Faculty(university_id=uni.id, name=payload.name, department=payload.department, expertise=payload.responsibilities)
    db.add(rec)
    db.commit()
    return {"id": rec.id}


@router.post("/students")
def add_student(payload: TeamMemberIn, user: User = Depends(_uni_user), db: Session = Depends(get_db)):
    from app.models import Student

    uni = user.university
    rec = Student(university_id=uni.id, name=payload.name, department=payload.department)
    db.add(rec)
    db.commit()
    return {"id": rec.id}
