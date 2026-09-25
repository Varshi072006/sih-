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


@router.get("/network")
def network(db: Session = Depends(get_db)):
    from app.models import UniversityOpinion, IndustryParticipation, GovernmentDepartment
    from app.api.ws import get_recent_events
    from datetime import datetime, timezone

    problems = db.query(Problem).filter(Problem.status.notin_(["submitted", "rejected"])).all()
    universities = db.query(University).filter(University.verification_status.in_(["verified", "activated"])).all()
    industries = db.query(Industry).filter(Industry.verification_status.in_(["verified", "activated"])).all()
    departments = db.query(GovernmentDepartment).all()
    opinions = db.query(UniversityOpinion).all()
    participations = db.query(IndustryParticipation).all()

    uni_map = {u.id: u for u in universities}
    ind_map = {i.id: i for i in industries}
    dept_map = {d.id: d for d in departments}
    prob_map = {p.id: p for p in problems}

    node_interactions = {}
    nodes = []
    links = []
    link_map = {}

    # 1. Government Departments
    dept_added = set()
    for p in problems:
        if p.assigned_department_id and p.assigned_department_id in dept_map:
            dept = dept_map[p.assigned_department_id]
            dept_node_id = f"DEPT-{dept.id}"
            if dept.id not in dept_added:
                dept_added.add(dept.id)
                nodes.append({
                    "id": dept_node_id,
                    "label": dept.name,
                    "type": "department",
                    "district": dept.district or "Statewide",
                    "interactionCount": 0,
                })
            src = f"P-{p.public_id}"
            tgt = dept_node_id
            key = (src, tgt, "assigned")
            if key not in link_map:
                link_obj = {
                    "source": src,
                    "target": tgt,
                    "type": "assigned",
                    "relationship": "Assigned Department",
                    "interactionCount": 1,
                    "latestActivity": "Department Assigned",
                }
                link_map[key] = link_obj
                links.append(link_obj)
            else:
                link_map[key]["interactionCount"] += 1
            node_interactions[src] = node_interactions.get(src, 0) + 1
            node_interactions[tgt] = node_interactions.get(tgt, 0) + 1

    # 2. Universities
    for u in universities:
        nodes.append({
            "id": f"UNI-{u.id}",
            "label": u.name[:28],
            "type": "university",
            "district": u.district or "Jharkhand",
            "interactionCount": 0,
        })

    # 3. Industries
    for i in industries:
        nodes.append({
            "id": f"IND-{i.id}",
            "label": i.company_name[:28],
            "type": "industry",
            "district": i.headquarters or "Jharkhand",
            "interactionCount": 0,
        })

    # 4. Problems
    for p in problems:
        nodes.append({
            "id": f"P-{p.public_id}",
            "label": p.title[:32],
            "type": "problem",
            "status": p.status,
            "district": p.district,
            "category": p.category,
            "interactionCount": 0,
        })

    # 5. Opinions
    for op in opinions:
        p = prob_map.get(op.problem_id)
        u = uni_map.get(op.university_id)
        if p and u:
            src = f"P-{p.public_id}"
            tgt = f"UNI-{u.id}"
            key = (src, tgt, "suggestion")
            if key not in link_map:
                link_obj = {
                    "source": src,
                    "target": tgt,
                    "type": "suggestion",
                    "relationship": "Suggestion",
                    "interactionCount": 1,
                    "latestActivity": "Suggestion Submitted",
                }
                link_map[key] = link_obj
                links.append(link_obj)
            else:
                link_map[key]["interactionCount"] += 1
            node_interactions[src] = node_interactions.get(src, 0) + 1
            node_interactions[tgt] = node_interactions.get(tgt, 0) + 1

    # 6. Participations
    for part in participations:
        p = prob_map.get(part.problem_id)
        i = ind_map.get(part.industry_id)
        if p and i:
            src = f"P-{p.public_id}"
            tgt = f"IND-{i.id}"
            ptype = (part.participation_types or "Collaboration").lower()
            rel_type = "investment" if "investment" in ptype or "funding" in ptype else "collaboration"
            key = (src, tgt, rel_type)
            if key not in link_map:
                link_obj = {
                    "source": src,
                    "target": tgt,
                    "type": rel_type,
                    "relationship": part.participation_types or "Industry Support",
                    "interactionCount": 1,
                    "latestActivity": "Industry Interest",
                }
                link_map[key] = link_obj
                links.append(link_obj)
            else:
                link_map[key]["interactionCount"] += 1
            node_interactions[src] = node_interactions.get(src, 0) + 1
            node_interactions[tgt] = node_interactions.get(tgt, 0) + 1

    for n in nodes:
        n["interactionCount"] = node_interactions.get(n["id"], 0)

    recent = get_recent_events(20)
    now_iso = datetime.now(timezone.utc).isoformat()
    if not recent:
        recent = [
            {
                "eventId": "evt-init-1",
                "type": "UNIVERSITY_SUGGESTION",
                "problemId": "P-C2I-001",
                "problemTitle": "Drinking Water Shortage",
                "universityName": "BIT Mesra",
                "timestamp": now_iso,
                "summary": "BIT Mesra submitted technical suggestion on Drinking Water Shortage",
            },
            {
                "eventId": "evt-init-2",
                "type": "DEPARTMENT_ASSIGNED",
                "problemId": "P-C2I-001",
                "problemTitle": "Drinking Water Shortage",
                "departmentName": "Drinking Water & Sanitation",
                "timestamp": now_iso,
                "summary": "Dept of Drinking Water assigned to Drinking Water Shortage",
            },
            {
                "eventId": "evt-init-3",
                "type": "INDUSTRY_INTEREST",
                "problemId": "P-C2I-002",
                "problemTitle": "Road Infrastructure Gap",
                "industryName": "Tata Steel",
                "timestamp": now_iso,
                "summary": "Tata Steel expressed CSR collaboration interest in Road Infrastructure",
            },
        ]

    return {"nodes": nodes, "links": links, "recentEvents": recent}


@router.get("/network/events")
def network_events():
    from app.api.ws import get_recent_events
    return get_recent_events(30)


@router.post("/network/emit-event")
def emit_network_event(data: dict):
    from app.api.ws import graph_event_bus
    event_type = data.get("type", "COLLABORATION_UPDATE")
    graph_event_bus.emit(event_type, data)
    return {"status": "emitted"}


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
