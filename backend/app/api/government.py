from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.ai.pipeline import analyze_problem, match_universities
from app.database.session import get_db
from app.models import (
    AIDuplicateMatch,
    AIUniversityRecommendation,
    GovernmentAction,
    GovernmentDepartment,
    GovernmentSolution,
    GovernmentSolutionVersion,
    Industry,
    Problem,
    ProblemAssignment,
    ProblemRelation,
    University,
    UniversityOpinion,
    User,
)
from app.schemas import AssignIn, DuplicateDecisionIn, OpinionReviewIn, RemarksIn, SolutionIn, UniversitySelectIn
from app.security.deps import client_meta, get_current_user, require_roles
from app.services.audit import AuditLogService
from app.services.notifications import NotificationService
from app.services.storage import save_upload
from app.services.workflow import transition_status
from app.utils.constants import ADMIN_ROLES, GOVERNMENT_ROLES, STATUS_LABELS
from app.api.problems import serialize_problem, _get

router = APIRouter(prefix="/api/government", tags=["Government"])


def _officer(user: User = Depends(require_roles(*GOVERNMENT_ROLES, *ADMIN_ROLES))) -> User:
    if user.primary_role in ADMIN_ROLES:
        return user
    if user.verification_status not in {"verified", "activated"}:
        raise HTTPException(status_code=403, detail="Government account is not verified")
    return user


@router.get("/dashboard")
def dashboard(user: User = Depends(_officer), db: Session = Depends(get_db)):
    def count(status=None):
        q = db.query(Problem)
        if status:
            q = q.filter(Problem.status == status)
        return q.count()

    districts = {}
    for p in db.query(Problem).all():
        districts[p.district] = districts.get(p.district, 0) + 1
    depts = {}
    for p in db.query(Problem).filter(Problem.assigned_department_id.isnot(None)).all():
        name = p.assigned_department.name if p.assigned_department else "Unassigned"
        depts[name] = depts.get(name, 0) + 1
    return {
        "total": count(),
        "pending_verification": count("pending_government_verification"),
        "verified": count("verified"),
        "assigned": count("assigned_to_department") + count("under_department_review"),
        "under_resolution": count("action_solution_uploaded") + count("ai_university_analysis"),
        "awaiting_university": count("universities_notified") + count("university_review"),
        "ready_for_industry": count("done_solution") + count("industry_participation"),
        "completed": count("completed"),
        "districts": districts,
        "departments": depts,
    }


@router.get("/departments")
def departments(user: User = Depends(_officer), db: Session = Depends(get_db)):
    return [{"id": d.id, "name": d.name, "code": d.code, "description": d.description} for d in db.query(GovernmentDepartment).all()]


@router.get("/problems")
def queue(
    status: str | None = None,
    district: str | None = None,
    department_id: int | None = None,
    category: str | None = None,
    q: str | None = None,
    user: User = Depends(_officer),
    db: Session = Depends(get_db),
):
    query = db.query(Problem)
    if status:
        query = query.filter(Problem.status == status)
    if district:
        query = query.filter(Problem.district == district)
    if department_id:
        query = query.filter(Problem.assigned_department_id == department_id)
    if category:
        query = query.filter(Problem.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter((Problem.title.ilike(like)) | (Problem.public_id.ilike(like)))
    return [serialize_problem(db, p, user) for p in query.order_by(Problem.id.desc()).all()]


@router.get("/problems/{problem_ref}")
def detail(problem_ref: str, user: User = Depends(_officer), db: Session = Depends(get_db)):
    return serialize_problem(db, _get(db, problem_ref), user, detail=True)


def _act(db, problem, user, action, remarks, ip, ua, payload="{}"):
    db.add(GovernmentAction(problem_id=problem.id, actor_id=user.id, action_type=action, remarks=remarks, payload=payload))
    AuditLogService.log(db, action.upper(), "problem", problem.public_id, user, details=remarks, ip_address=ip, user_agent=ua)


@router.post("/problems/{problem_ref}/verify")
def verify(problem_ref: str, payload: RemarksIn, request: Request, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    ip, ua = client_meta(request)
    analyze_problem(db, p)
    transition_status(db, p, "verified", user, payload.remarks or "Verified")
    p.official_remarks = payload.remarks
    _act(db, p, user, "verify", payload.remarks, ip, ua)
    NotificationService.notify_user(db, p.citizen_id, "problem", "Problem verified", f"{p.public_id} has been verified.", "problem", p.public_id)
    db.commit()
    return {"status": p.status, "status_label": STATUS_LABELS[p.status]}


@router.post("/problems/{problem_ref}/reject")
def reject(problem_ref: str, payload: RemarksIn, request: Request, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    ip, ua = client_meta(request)
    transition_status(db, p, "rejected", user, payload.remarks or "Rejected")
    p.official_remarks = payload.remarks
    _act(db, p, user, "reject", payload.remarks, ip, ua)
    NotificationService.notify_user(db, p.citizen_id, "problem", "Problem rejected", f"{p.public_id}: {payload.remarks}", "problem", p.public_id)
    db.commit()
    return {"status": p.status}


@router.post("/problems/{problem_ref}/request-info")
def request_info(problem_ref: str, payload: RemarksIn, request: Request, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    ip, ua = client_meta(request)
    _act(db, p, user, "request_more_information", payload.remarks, ip, ua)
    NotificationService.notify_user(db, p.citizen_id, "problem", "More information required", payload.remarks, "problem", p.public_id)
    db.commit()
    return {"message": "Request sent to citizen"}


@router.post("/problems/{problem_ref}/assign")
def assign(problem_ref: str, payload: AssignIn, request: Request, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    dept = db.get(GovernmentDepartment, payload.department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    ip, ua = client_meta(request)
    if p.status == "verified":
        transition_status(db, p, "assigned_to_department", user, payload.remarks)
        transition_status(db, p, "under_department_review", user, "Department review started")
    elif p.status == "assigned_to_department":
        transition_status(db, p, "under_department_review", user, payload.remarks)
    p.assigned_department_id = dept.id
    db.add(ProblemAssignment(problem_id=p.id, department_id=dept.id, assigned_by_id=user.id, remarks=payload.remarks))
    _act(db, p, user, "assign", payload.remarks, ip, ua)
    NotificationService.notify_user(db, p.citizen_id, "problem", "Department assigned", f"{p.public_id} assigned to {dept.name}", "problem", p.public_id)
    db.commit()
    return {"status": p.status, "department": dept.name}


@router.post("/problems/{problem_ref}/duplicate")
def duplicate_decision(problem_ref: str, payload: DuplicateDecisionIn, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    if payload.decision not in {"related", "merged", "separate"}:
        raise HTTPException(status_code=400, detail="Decision must be related, merged or separate")
    db.add(
        ProblemRelation(
            problem_id=p.id,
            related_problem_id=payload.related_problem_id,
            relation_type=payload.decision,
            decided_by_id=user.id,
            reason=payload.reason,
        )
    )
    match = (
        db.query(AIDuplicateMatch)
        .filter(AIDuplicateMatch.problem_id == p.id, AIDuplicateMatch.matched_problem_id == payload.related_problem_id)
        .first()
    )
    if match:
        match.human_decision = payload.decision
    AuditLogService.log(db, "UPDATE", "problem_relation", p.public_id, user, details=payload.decision)
    db.commit()
    return {"message": "Duplicate decision recorded. AI did not merge records automatically."}


@router.post("/problems/{problem_ref}/solution")
def upload_solution(
    problem_ref: str,
    request: Request,
    description: str = Form(...),
    action_taken: str = Form(...),
    implementation_details: str = Form(""),
    files: list[UploadFile] | None = File(None),
    user: User = Depends(_officer),
    db: Session = Depends(get_db),
):
    p = _get(db, problem_ref)
    sol = db.query(GovernmentSolution).filter(GovernmentSolution.problem_id == p.id).first()
    if not sol:
        sol = GovernmentSolution(problem_id=p.id, current_version=0)
        db.add(sol)
        db.flush()
    attachments = []
    for f in files or []:
        if not f or not f.filename:
            continue
        stored = save_upload(db, f, user.id, "government_solution", str(p.id))
        attachments.append(stored.id)
    version = sol.current_version + 1
    db.add(
        GovernmentSolutionVersion(
            solution_id=sol.id,
            version=version,
            description=description,
            action_taken=action_taken,
            implementation_details=implementation_details,
            uploaded_by_id=user.id,
            attachments_json=str(attachments),
        )
    )
    sol.current_version = version
    ip, ua = client_meta(request)
    if p.status == "under_department_review":
        transition_status(db, p, "action_solution_uploaded", user, f"Government Solution v{version}")
        transition_status(db, p, "ai_university_analysis", user, "AI university matching started")
    elif p.status in {"government_review", "university_opinion_submitted", "no_opinion", "solution_updated"}:
        if p.status != "solution_updated":
            try:
                transition_status(db, p, "solution_updated", user, f"Government Solution v{version}")
            except HTTPException:
                p.status = "solution_updated"
    match_universities(db, p, f"{description} {action_taken}")
    _act(db, p, user, "upload_solution", f"v{version}", ip, ua)
    NotificationService.notify_user(db, p.citizen_id, "problem", "Government action uploaded", f"Solution v{version} recorded for {p.public_id}", "problem", p.public_id)
    NotificationService.notify_role(db, "admin", "ai", "University recommendations ready", p.public_id, "problem", p.public_id)
    db.commit()
    return {"version": version, "status": p.status, "message": f"Government Solution v{version} saved. Previous versions were preserved."}


@router.post("/problems/{problem_ref}/select-universities")
def select_universities(problem_ref: str, payload: UniversitySelectIn, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    recs = db.query(AIUniversityRecommendation).filter(AIUniversityRecommendation.problem_id == p.id).all()
    selected_ids = set(payload.university_ids)
    for r in recs:
        r.selected = r.university_id in selected_ids
        r.selected_by_id = user.id if r.selected else None
        if r.selected:
            uni = db.get(University, r.university_id)
            if uni:
                NotificationService.notify_university(
                    db,
                    uni.id,
                    notification_type="problem",
                    title="Problem available for review",
                    message=f"Government solution uploaded for {p.public_id}. Your institution was selected for review.",
                    entity_type="problem",
                    entity_id=p.public_id,
                )
    if p.status == "ai_university_analysis":
        transition_status(db, p, "universities_notified", user, "Selected universities notified")
        transition_status(db, p, "university_review", user, "Awaiting university review")
    AuditLogService.log(db, "APPROVE", "university_selection", p.public_id, user, details=str(payload.university_ids))
    db.commit()
    return {"status": p.status, "selected": list(selected_ids)}


@router.post("/opinions/{opinion_id}/review")
def review_opinion(opinion_id: int, payload: OpinionReviewIn, request: Request, user: User = Depends(_officer), db: Session = Depends(get_db)):
    op = db.get(UniversityOpinion, opinion_id)
    if not op:
        raise HTTPException(status_code=404, detail="Opinion not found")
    if payload.decision not in {"accept", "partial", "reject", "clarification"}:
        raise HTTPException(status_code=400, detail="Invalid decision")
    op.government_decision = payload.decision
    op.government_remarks = payload.remarks
    p = db.get(Problem, op.problem_id)
    ip, ua = client_meta(request)
    if p.status in {"university_opinion_submitted", "university_review", "no_opinion"}:
        try:
            transition_status(db, p, "government_review", user, payload.remarks)
        except HTTPException:
            pass
    if payload.update_solution and payload.solution:
        sol = db.query(GovernmentSolution).filter(GovernmentSolution.problem_id == p.id).first()
        if sol:
            version = sol.current_version + 1
            db.add(
                GovernmentSolutionVersion(
                    solution_id=sol.id,
                    version=version,
                    description=payload.solution.description,
                    action_taken=payload.solution.action_taken,
                    implementation_details=payload.solution.implementation_details,
                    uploaded_by_id=user.id,
                )
            )
            sol.current_version = version
            if p.status == "government_review":
                transition_status(db, p, "solution_updated", user, f"Solution v{version} after university opinion")
    uni = db.get(University, op.university_id)
    if uni:
        NotificationService.notify_university(
            db,
            uni.id,
            notification_type="problem",
            title="Government response to opinion",
            message=f"{payload.decision} for {p.public_id}",
            entity_type="problem",
            entity_id=p.public_id,
        )
    AuditLogService.log(db, "UPDATE", "university_opinion", str(opinion_id), user, details=payload.decision, ip_address=ip, user_agent=ua)
    db.commit()
    return {"message": "Opinion reviewed", "status": p.status}


@router.post("/problems/{problem_ref}/done-solution")
def done_solution(problem_ref: str, payload: RemarksIn, request: Request, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    sol = db.query(GovernmentSolution).filter(GovernmentSolution.problem_id == p.id).first()
    if not sol:
        raise HTTPException(status_code=400, detail="Upload a solution before marking it done")
    if p.status not in {"government_review", "solution_updated", "no_opinion", "university_opinion_submitted"}:
        # allow from government_review pathway; try transition
        pass
    if p.status in {"university_opinion_submitted", "no_opinion"}:
        try:
            transition_status(db, p, "government_review", user, "Final review before done solution")
        except HTTPException:
            pass
    transition_status(db, p, "done_solution", user, payload.remarks or "Marked done solution")
    sol.is_done = True
    sol.done_by_id = user.id
    sol.done_at = datetime.now(timezone.utc)
    ip, ua = client_meta(request)
    _act(db, p, user, "done_solution", payload.remarks, ip, ua)
    NotificationService.notify_user(db, p.citizen_id, "problem", "Solution marked done", f"{p.public_id} is available for optional industry participation.", "problem", p.public_id)
    for org in db.query(Industry).filter(Industry.verification_status.in_(["verified", "activated"])).all():
        NotificationService.notify_industry(
            db,
            org.id,
            notification_type="problem",
            title="Problem available for participation",
            message=f"{p.public_id} is open for optional industry collaboration.",
            entity_type="problem",
            entity_id=p.public_id,
        )
    db.commit()
    return {"status": p.status, "message": "Solution marked complete and published to industry participation queue."}


@router.post("/problems/{problem_ref}/complete")
def complete(problem_ref: str, payload: RemarksIn, request: Request, user: User = Depends(_officer), db: Session = Depends(get_db)):
    p = _get(db, problem_ref)
    if p.status == "done_solution":
        transition_status(db, p, "industry_participation", user, "Industry window opened (optional)")
    if p.status == "industry_participation":
        transition_status(db, p, "implementation_pilot", user, payload.remarks or "Implementation")
    transition_status(db, p, "completed", user, payload.remarks or "Problem completed")
    NotificationService.notify_user(db, p.citizen_id, "problem", "Problem completed", f"{p.public_id} has been marked completed.", "problem", p.public_id)
    db.commit()
    return {"status": p.status}


@router.post("/proposals/{proposal_id}/review")
def review_proposal(proposal_id: int, payload: RemarksIn, decision: str = "accept", user: User = Depends(_officer), db: Session = Depends(get_db)):
    from app.models import IndustryProposal

    pr = db.get(IndustryProposal, proposal_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Proposal not found")
    pr.review_status = decision
    pr.review_remarks = payload.remarks
    AuditLogService.log(db, "APPROVE" if decision == "accept" else "REJECT", "industry_proposal", str(proposal_id), user, details=payload.remarks)
    db.commit()
    return {"message": "Proposal reviewed", "status": pr.review_status}
