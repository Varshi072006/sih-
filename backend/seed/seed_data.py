from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ai.pipeline import analyze_problem, match_universities
from app.models import (
    AIUniversityRecommendation,
    Citizen,
    CitizenFeedback,
    Faculty,
    GovernmentDepartment,
    GovernmentSolution,
    GovernmentSolutionVersion,
    GovernmentUser,
    ImpactMetric,
    Industry,
    IndustryCapability,
    IndustryParticipation,
    IndustryProposal,
    Notification,
    Problem,
    ProblemEvidence,
    ProblemLocation,
    ProblemStatusHistory,
    Project,
    ProjectMember,
    ProjectMilestone,
    Role,
    Student,
    University,
    UniversityDepartment,
    UniversityOpinion,
    UniversityReview,
    User,
    UserRole,
)
from app.security.auth import hash_password
from app.services.ids import next_problem_public_id, next_project_public_id
from app.utils.constants import MILESTONE_NAMES, ROLES

DEMO_PASSWORD = "Demo@1234"


def seed_all(db: Session) -> None:
    if db.query(Role).count() == 0:
        for name in ROLES:
            db.add(Role(name=name, description=name.replace("_", " ").title()))
        db.flush()

    depts = [
        ("WRD", "Water Resources / Rural Water Supply", "Drinking water, irrigation and quality"),
        ("RD", "Rural Development", "Rural roads, livelihoods and infrastructure"),
        ("EDU", "Education Department", "Schools and learning outcomes"),
        ("HLT", "Health Department", "Primary and public health"),
        ("AGR", "Agriculture Department", "Crops, extension and agri-innovation"),
        ("ULB", "Urban Local Body / Municipality", "Waste, sanitation and urban services"),
        ("ENE", "Energy Department", "Electrification and renewables"),
        ("FOR", "Forest, Environment & Climate Change", "Environment and disaster monitoring"),
        ("SW", "Social Welfare", "Accessibility and inclusion"),
        ("ADM", "District Administration", "Coordination and public administration"),
    ]
    if db.query(GovernmentDepartment).count() == 0:
        for code, name, desc in depts:
            db.add(GovernmentDepartment(code=code, name=name, description=desc))
        db.flush()

    if db.query(User).filter(User.email == "admin@c2i.jharkhand.gov.in").first():
        seed_extended_demo_data(db)
        db.commit()
        return

    def add_user(email, name, role, mobile="9876543210", verified="verified", demo=True):
        user = User(
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            full_name=name,
            mobile=mobile,
            primary_role=role,
            verification_status=verified,
            is_demo=demo,
            is_active=True,
        )
        db.add(user)
        db.flush()
        role_row = db.query(Role).filter(Role.name == role).first()
        if role_row:
            db.add(UserRole(user_id=user.id, role_id=role_row.id))
        return user

    admin = add_user("admin@c2i.jharkhand.gov.in", "Demo Admin", "admin")
    add_user("superadmin@c2i.jharkhand.gov.in", "Demo Super Admin", "super_admin")
    citizen = add_user("citizen@demo.in", "Demo Citizen", "citizen", verified="activated")
    db.add(Citizen(user_id=citizen.id, district="Ranchi", block="Namkum", village="Angara", address="Ward 12, Angara"))
    gov = add_user("gov@demo.in", "Demo Government Officer", "government_officer")
    water = db.query(GovernmentDepartment).filter(GovernmentDepartment.code == "WRD").first()
    db.add(GovernmentUser(user_id=gov.id, official_id="JH-GOV-1001", designation="Executive Engineer", department_id=water.id if water else None, district="Ranchi", jurisdiction="Ranchi district"))

    uni_user = add_user("university@demo.in", "Registrar, Demo University 1", "university")
    uni1 = University(
        user_id=uni_user.id,
        name="Demo University 1",
        institution_type="University",
        official_id="UNI-DEMO-001",
        address="Ranchi",
        district="Ranchi",
        website="https://example.edu",
        contact_person="Registrar, Demo University 1",
        phone="0651-000001",
        faculty_expertise="Water quality, civil engineering, public health, remote sensing",
        research_areas="Rural water, IoT sensing, community health",
        laboratories="Water Quality Lab; IoT Prototyping Lab",
        innovation_centre="Demo Innovation Centre",
        incubation_centre="Demo Incubation Centre",
        previous_projects="Village water quality dashboard; rural road condition mapping",
        technologies="IoT, GIS, computer vision",
        verification_status="verified",
        is_demo=True,
    )
    db.add(uni1)
    db.flush()
    for n in ["Civil Engineering", "Computer Science", "Environmental Science"]:
        db.add(UniversityDepartment(university_id=uni1.id, name=n))
    db.add(Faculty(university_id=uni1.id, name="Dr. A. Sharma", department="Civil Engineering", expertise="Water treatment"))
    db.add(Student(university_id=uni1.id, name="R. Kisku", department="Computer Science"))

    uni2u = add_user("engineering@demo.in", "Dean, Demo Engineering Institute", "university")
    uni2 = University(
        user_id=uni2u.id,
        name="Demo Engineering Institute",
        institution_type="Engineering College",
        official_id="UNI-DEMO-002",
        address="Jamshedpur",
        district="East Singhbhum",
        contact_person="Dean, Demo Engineering Institute",
        phone="0657-000002",
        faculty_expertise="Civil, ECE, transportation, structural health monitoring",
        research_areas="Rural infrastructure, sensors, embedded systems",
        laboratories="Structures Lab; Embedded Systems Lab",
        previous_projects="Road monitoring prototype; solar microgrid pilot",
        technologies="Sensors, computer vision, solar",
        verification_status="verified",
        is_demo=True,
    )
    db.add(uni2)
    db.flush()
    for n in ["Civil Engineering", "ECE", "Mechanical"]:
        db.add(UniversityDepartment(university_id=uni2.id, name=n))

    uni3u = add_user("agri@demo.in", "Dean, Demo Agriculture University", "university")
    uni3 = University(
        user_id=uni3u.id,
        name="Demo Agriculture University",
        institution_type="Agriculture University",
        official_id="UNI-DEMO-003",
        address="Kanke, Ranchi",
        district="Ranchi",
        contact_person="Dean, Demo Agriculture University",
        phone="0651-000003",
        faculty_expertise="Plant pathology, agronomy, agri-informatics",
        research_areas="Crop disease, climate-resilient farming",
        laboratories="Plant Pathology Lab; GIS Lab",
        previous_projects="Paddy disease detection trial",
        technologies="Computer vision, remote sensing",
        verification_status="verified",
        is_demo=True,
    )
    db.add(uni3)
    db.flush()
    db.add(UniversityDepartment(university_id=uni3.id, name="Plant Pathology"))

    ind1u = add_user("iot@demo.in", "Demo IoT Solutions", "industry")
    ind1 = Industry(
        user_id=ind1u.id,
        company_name="Demo IoT Solutions",
        organization_type="startup",
        sector="DeepTech / IoT",
        registration_details="DEMO-CIN-0001",
        district="Ranchi",
        contact_person="Ops Lead",
        phone="9000000001",
        technical_expertise="Low-cost water sensors and dashboards",
        products_services="Monitoring kits",
        technologies="IoT, LoRa, cloud dashboards",
        csr_areas="Safe drinking water",
        verification_status="verified",
        is_demo=True,
    )
    db.add(ind1)
    db.flush()
    for cap in ["prototype", "testing", "deployment", "mentorship"]:
        db.add(IndustryCapability(industry_id=ind1.id, name=cap, enabled=True))

    ind2u = add_user("agritech@demo.in", "Demo AgriTech Startup", "startup")
    ind2 = Industry(
        user_id=ind2u.id,
        company_name="Demo AgriTech Startup",
        organization_type="startup",
        sector="Agriculture",
        district="Hazaribagh",
        contact_person="Founder",
        phone="9000000002",
        technical_expertise="Crop disease imaging",
        technologies="Computer vision",
        csr_areas="Farmer livelihoods",
        verification_status="verified",
        is_demo=True,
    )
    db.add(ind2)
    db.flush()

    ind3u = add_user("energy@demo.in", "Demo Renewable Energy Company", "industry")
    ind3 = Industry(
        user_id=ind3u.id,
        company_name="Demo Renewable Energy Company",
        organization_type="industry",
        sector="Energy",
        district="Dhanbad",
        contact_person="CSR Head",
        phone="9000000003",
        technical_expertise="Solar microgrids",
        technologies="Solar PV, storage",
        csr_areas="Rural electrification",
        verification_status="verified",
        is_demo=True,
    )
    db.add(ind3)
    db.flush()
    db.add(IndustryCapability(industry_id=ind3.id, name="funding", enabled=True))
    db.add(IndustryCapability(industry_id=ind3.id, name="deployment", enabled=True))

    samples = [
        ("Drinking water contamination in Angara", "Village drinking water from the community well is contaminated and families report illness after consumption.", "Water Management", "Drinking Water Quality", "Ranchi", "Namkum", "Angara", 23.37, 85.44, 500, "high", "high", "pending_government_verification"),
        ("Rural road damage on Khunti connector", "The connector road is severely damaged after monsoon, limiting ambulance and school access.", "Urban Infrastructure", "Roads", "Khunti", "Khunti", "Torpa", 23.07, 85.27, 1200, "high", "high", "under_department_review"),
        ("Crop disease in paddy fields", "Farmers report spreading leaf blight in paddy requiring rapid detection support.", "Agriculture", "Crop Disease", "Hazaribagh", "Ichak", "Ichak", 24.00, 85.36, 800, "medium", "high", "action_solution_uploaded"),
        ("School attendance monitoring gap", "Upper primary school lacks a reliable attendance process and dropout risk is rising.", "Education", "Attendance", "Dumka", "Dumka", "Kathikund", 24.26, 87.25, 320, "medium", "medium", "university_review"),
        ("Waste management in municipal ward", "Uncollected waste is accumulating near the market affecting sanitation.", "Sanitation", "Waste", "Dhanbad", "Dhanbad", "Jharia", 23.74, 86.41, 2000, "high", "medium", "done_solution"),
        ("Rural healthcare access after sunset", "The PHC has no reliable emergency transport after 6 pm.", "Healthcare", "Ambulance", "Latehar", "Latehar", "Balumath", 23.74, 84.50, 900, "critical", "high", "industry_participation"),
        ("Flood monitoring for low-lying hamlets", "Seasonal flooding arrives with little local warning for riverside hamlets.", "Environment", "Disaster", "Sahibganj", "Rajmahal", "Rajmahal", 25.05, 87.84, 1500, "high", "high", "completed"),
        ("Solar energy for unelectrified hamlet", "A forest-fringe hamlet has unreliable grid supply and needs community solar.", "Energy", "Solar", "Gumla", "Bishunpur", "Bishunpur", 23.43, 84.52, 180, "medium", "medium", "verified"),
    ]

    created = []
    year = datetime.now(timezone.utc).year
    for i, s in enumerate(samples, start=1):
        title, desc, cat, sub, dist, block, village, lat, lng, pop, sev, urg, status = s
        p = Problem(
            public_id=f"JH-PR-{year}-{i:05d}",
            citizen_id=citizen.id,
            title=title,
            description=desc,
            category=cat,
            subcategory=sub,
            expected_solution="Locally appropriate, maintainable public solution.",
            affected_people_description="Households in the reported locality.",
            district=dist,
            block=block,
            village=village,
            address=f"{village}, {dist}",
            latitude=lat,
            longitude=lng,
            estimated_affected_population=pop,
            severity=sev,
            urgency=urg,
            geographic_impact="village",
            status=status,
            is_demo=True,
            assigned_department_id=water.id if water and cat == "Water Management" else (db.query(GovernmentDepartment).first().id if db.query(GovernmentDepartment).first() else None),
        )
        db.add(p)
        db.flush()
        db.add(ProblemLocation(problem_id=p.id, district=dist, block=block, village=village, address=p.address, latitude=lat, longitude=lng, source="map_selection"))
        db.add(ProblemStatusHistory(problem_id=p.id, previous_status="submitted", new_status=status, actor_id=gov.id, note="DEMO DATA seed status"))
        created.append(p)

    for p in created:
        analyze_problem(db, p)

    # richer workflow for water problem
    water_p = created[0]
    # leave pending verification for government queue demo

    road = created[1]
    db.add(GovernmentSolution(problem_id=road.id, current_version=1))
    db.flush()

    crop = created[2]
    sol = GovernmentSolution(problem_id=crop.id, current_version=1)
    db.add(sol)
    db.flush()
    db.add(GovernmentSolutionVersion(solution_id=sol.id, version=1, description="Extension advisory issued and sampling planned.", action_taken="Block agriculture office notified farmers.", implementation_details="Field visit scheduled.", uploaded_by_id=gov.id))
    match_universities(db, crop, "crop disease detection")
    recs = db.query(AIUniversityRecommendation).filter(AIUniversityRecommendation.problem_id == crop.id).all()
    for r in recs[:1]:
        r.selected = True

    school = created[3]
    db.add(UniversityReview(problem_id=school.id, university_id=uni1.id, reviewer_id=uni_user.id, decision="review", note="Reviewing attendance process."))
    db.add(UniversityOpinion(problem_id=school.id, university_id=uni1.id, author_id=uni_user.id, suggestion="Pilot a privacy-preserving digital attendance register with teacher confirmation.", recommended_improvement="Avoid biometric mandate in first phase.", technical_recommendation="Offline-first mobile form with daily sync.", expected_benefit="Earlier dropout alerts."))

    waste = created[4]
    wsol = GovernmentSolution(problem_id=waste.id, current_version=1, is_done=True, done_by_id=gov.id, done_at=datetime.now(timezone.utc))
    db.add(wsol)
    db.flush()
    db.add(GovernmentSolutionVersion(solution_id=wsol.id, version=1, description="Ward collection roster published.", action_taken="Additional collection trip assigned.", uploaded_by_id=gov.id))

    health = created[5]
    part = IndustryParticipation(problem_id=health.id, industry_id=ind1.id, participation_types="Technology,Prototype", status="expressed_interest")
    db.add(part)
    db.flush()
    db.add(IndustryProposal(participation_id=part.id, problem_id=health.id, industry_id=ind1.id, proposal="Pilot GPS-enabled referral coordination for evening emergencies.", technology_offered="Lightweight dispatch app", estimated_budget="Demo estimate", timeline="12 weeks", expected_contribution="Prototype and training"))

    flood = created[6]
    proj = Project(
        public_id=f"JH-PJ-{year}-00001",
        problem_id=flood.id,
        university_id=uni2.id,
        industry_id=ind1.id,
        department_id=db.query(GovernmentDepartment).filter(GovernmentDepartment.code == "FOR").first().id,
        title="Community flood early-warning pilot (DEMO DATA)",
        objectives="Local water-level alerts for riverside hamlets.",
        technology="Ultrasonic level sensors and SMS alerts",
        budget="Demo",
        timeline="6 months",
        status="completed",
        is_demo=True,
        completed_at=datetime.now(timezone.utc) - timedelta(days=20),
        final_outcome="Alert coverage for 1500 residents in the demo scenario.",
    )
    db.add(proj)
    db.flush()
    db.add(ProjectMember(project_id=proj.id, name="Dr. A. Sharma", member_type="faculty", department="Civil Engineering", role="Mentor"))
    db.add(ProjectMember(project_id=proj.id, name="R. Kisku", member_type="student", department="Computer Science", role="Developer"))
    for i, name in enumerate(MILESTONE_NAMES, start=1):
        db.add(ProjectMilestone(project_id=proj.id, name=name, sequence=i, status="completed", approved=True, description=f"{name} complete (DEMO DATA)"))
    db.add(
        ImpactMetric(
            problem_id=flood.id,
            project_id=proj.id,
            people_benefited=1500,
            geographic_coverage="Rajmahal riverside hamlets",
            technology_deployed="Community flood sensors (demo)",
            before_text="1500 residents in low-lying hamlets received little local flood warning.",
            solution_text="Community water-level sensors with SMS alerts (DEMO DATA).",
            after_text="1500 residents covered by a local warning channel in this demonstration scenario.",
            patents=0,
            publications=1,
            startups_created=0,
            technologies_transferred=1,
            verified=False,
            is_demo=True,
        )
    )
    project_examples = [
        {
            "public_id": f"JH-PJ-{year}-00002",
            "problem_id": school.id,
            "university_id": uni1.id,
            "industry_id": ind2.id,
            "title": "Offline-first school attendance pilot (DEMO DATA)",
            "objectives": "Improve early identification of attendance and dropout risk without requiring continuous connectivity.",
            "technology": "Offline-first teacher workflow with district-level reporting",
            "timeline": "4 months",
            "status": "active",
        },
        {
            "public_id": f"JH-PJ-{year}-00003",
            "problem_id": crop.id,
            "university_id": uni3.id,
            "industry_id": ind2.id,
            "title": "Paddy disease image advisory pilot (DEMO DATA)",
            "objectives": "Test low-cost crop image collection and advisory support for smallholder farmers.",
            "technology": "Mobile crop imaging and computer-vision triage",
            "timeline": "5 months",
            "status": "implementation_pilot",
        },
    ]
    for example in project_examples:
        project = Project(
            **example,
            department_id=water.id if water else None,
            budget="Demo implementation budget",
            is_demo=True,
        )
        db.add(project)
        db.flush()
        db.add(ProjectMember(project_id=project.id, name="University research team", member_type="faculty", department="Applied Research", role="Technical lead"))
        for sequence, name in enumerate(MILESTONE_NAMES, start=1):
            db.add(ProjectMilestone(project_id=project.id, name=name, sequence=sequence, status="in_progress" if sequence == 1 else "pending", approved=False, description=f"{name} milestone (DEMO DATA)"))

    db.add(CitizenFeedback(problem_id=flood.id, citizen_id=citizen.id, satisfaction=4, resolved=True, comments="Warning messages helped families move livestock earlier. DEMO DATA."))

    NotificationService_seed(db, citizen.id, gov.id, uni_user.id, ind1u.id, admin.id, water_p.public_id)
    seed_extended_demo_data(db)
    db.commit()


def NotificationService_seed(db, citizen_id, gov_id, uni_id, ind_id, admin_id, pid):
    rows = [
        (citizen_id, "problem", "Problem submitted", f"Tracking ID {pid} is pending government verification."),
        (gov_id, "problem", "New problem", f"New citizen problem {pid} requires verification."),
        (uni_id, "problem", "Problem available for review", "A government solution is ready for academic review (DEMO DATA)."),
        (ind_id, "problem", "Problem available for participation", "Optional industry participation is open on a done-solution problem (DEMO DATA)."),
        (admin_id, "registration", "Demo platform ready", "Seeded demo users, problems and projects. All organisational records are labelled DEMO DATA."),
    ]
    for rid, typ, title, msg in rows:
        db.add(Notification(recipient_id=rid, notification_type=typ, title=title, message=msg, entity_type="problem", entity_id=pid))


def seed_extended_demo_data(db: Session) -> None:
    """Add the public-facing demo catalogue without duplicating existing rows."""
    citizen = db.query(User).filter(User.email == "citizen@demo.in").first()
    gov = db.query(User).filter(User.email == "gov@demo.in").first()
    if not citizen or not gov:
        return

    def get_or_add_user(email, name, role):
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user
        user = User(
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            full_name=name,
            mobile="98765432%04d" % (db.query(User).count() + 1),
            primary_role=role,
            verification_status="verified",
            is_demo=True,
            is_active=True,
        )
        db.add(user)
        db.flush()
        role_row = db.query(Role).filter(Role.name == role).first()
        if role_row:
            db.add(UserRole(user_id=user.id, role_id=role_row.id))
        return user

    uni_user = get_or_add_user("research@demo.in", "Director, Demo Research University", "university")
    uni = db.query(University).filter(University.name == "Demo Research University").first()
    if not uni:
        uni = University(
            user_id=uni_user.id,
            name="Demo Research University",
            institution_type="University",
            official_id="UNI-DEMO-004",
            address="Morabadi, Ranchi",
            district="Ranchi",
            website="https://research.example.edu",
            contact_person="Director, Demo Research University",
            phone="0651-000004",
            faculty_expertise="Climate science, public health, geospatial analytics",
            research_areas="Climate resilience, GIS, rural innovation",
            laboratories="Climate Data Lab; Public Systems Lab",
            technologies="GIS, satellite analytics, open data",
            verification_status="verified",
            is_demo=True,
        )
        db.add(uni)
        db.flush()
        db.add(UniversityDepartment(university_id=uni.id, name="Geospatial Analytics"))
        db.add(UniversityDepartment(university_id=uni.id, name="Public Health"))

    industry_specs = [
        ("mobility@demo.in", "Demo Mobility Systems", "Mobility", "Electric mobility and emergency logistics", "EVs, routing, fleet analytics", "Emergency transport"),
        ("climate@demo.in", "Demo Climate Analytics", "ClimateTech", "Flood forecasting and climate risk mapping", "Satellite data, GIS, dashboards", "Climate resilience"),
    ]
    industries = []
    for email, name, sector, expertise, technologies, csr in industry_specs:
        user = get_or_add_user(email, name, "industry")
        industry = db.query(Industry).filter(Industry.company_name == name).first()
        if not industry:
            industry = Industry(
                user_id=user.id,
                company_name=name,
                organization_type="industry",
                sector=sector,
                registration_details="DEMO-REG-%s" % email.split("@")[0].upper(),
                district="Ranchi",
                contact_person="Demo Partnerships Lead",
                phone="90000000%02d" % (len(industries) + 4),
                technical_expertise=expertise,
                products_services="Public-sector pilot and deployment services",
                technologies=technologies,
                csr_areas=csr,
                verification_status="verified",
                is_demo=True,
            )
            db.add(industry)
            db.flush()
            db.add(IndustryCapability(industry_id=industry.id, name="deployment", enabled=True))
            db.add(IndustryCapability(industry_id=industry.id, name="mentorship", enabled=True))
        industries.append(industry)

    department = db.query(GovernmentDepartment).filter(GovernmentDepartment.code == "FOR").first()
    problem_specs = [
        ("Heatwave alert access for outdoor workers", "Outdoor workers need timely local heat alerts and hydration guidance.", "Healthcare", "Public Health", "Ranchi", "Kanke", "Kanke", 23.47, 85.32, 650, "high", "high", "verified"),
        ("Last-mile emergency transport coordination", "Remote settlements face long delays finding transport to the nearest health facility.", "Healthcare", "Ambulance", "Simdega", "Simdega", "Thethaitangar", 22.62, 84.50, 1100, "critical", "high", "under_department_review"),
        ("Community air-quality information gap", "Residents near a busy industrial corridor lack accessible local air-quality information.", "Environment", "Air Quality", "Bokaro", "Chas", "Chas", 23.64, 86.13, 1800, "medium", "medium", "completed"),
    ]
    problems = []
    for title, desc, category, subcategory, district, block, village, lat, lng, population, severity, urgency, status in problem_specs:
        problem = db.query(Problem).filter(Problem.title == title).first()
        if not problem:
            problem = Problem(
                public_id=next_problem_public_id(db),
                citizen_id=citizen.id,
                title=title,
                description=desc,
                category=category,
                subcategory=subcategory,
                expected_solution="A practical, community-tested public service pilot.",
                affected_people_description="Residents and workers in the reported locality.",
                district=district,
                block=block,
                village=village,
                address=f"{village}, {district}",
                latitude=lat,
                longitude=lng,
                estimated_affected_population=population,
                severity=severity,
                urgency=urgency,
                geographic_impact="village",
                status=status,
                is_demo=True,
                assigned_department_id=department.id if department else None,
            )
            db.add(problem)
            db.flush()
            db.add(ProblemLocation(problem_id=problem.id, district=district, block=block, village=village, address=problem.address, latitude=lat, longitude=lng, source="map_selection"))
            db.add(ProblemStatusHistory(problem_id=problem.id, previous_status="submitted", new_status=status, actor_id=gov.id, note="DEMO DATA seed status"))
            analyze_problem(db, problem)
        problems.append(problem)

    project_specs = [
        ("Heat resilience outreach pilot", problems[0], uni, industries[0], "active", "Heat alerts and hydration support for outdoor workers."),
        ("Community air-quality dashboard pilot", problems[2], uni, industries[1], "completed", "A public dashboard and ward-level reporting workflow."),
    ]
    for title, problem, university, industry, status, outcome in project_specs:
        if db.query(Project).filter(Project.title == title).first():
            continue
        project = Project(
            public_id=next_project_public_id(db),
            problem_id=problem.id,
            university_id=university.id,
            industry_id=industry.id,
            department_id=department.id if department else None,
            title=title,
            objectives="Test an accountable, locally maintainable solution with public reporting.",
            technology="Open data dashboard, field reporting and community feedback",
            budget="Demo implementation budget",
            timeline="6 months",
            status=status,
            is_demo=True,
            completed_at=datetime.now(timezone.utc) - timedelta(days=12) if status == "completed" else None,
            final_outcome=outcome if status == "completed" else "Pilot is active in the demo scenario.",
        )
        db.add(project)
        db.flush()
        for sequence, name in enumerate(MILESTONE_NAMES, start=1):
            complete = status == "completed"
            db.add(ProjectMilestone(project_id=project.id, name=name, sequence=sequence, status="completed" if complete else ("in_progress" if sequence == 1 else "pending"), approved=complete, description=f"{name} milestone (DEMO DATA)"))
