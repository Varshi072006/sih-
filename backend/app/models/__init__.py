from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    mobile: Mapped[str] = mapped_column(String(20), default="")
    primary_role: Mapped[str] = mapped_column(String(64), index=True)
    verification_status: Mapped[str] = mapped_column(String(64), default="pending_verification", index=True)
    account_status: Mapped[str] = mapped_column(String(64), default="active")
    aadhaar_verification_status: Mapped[str] = mapped_column(String(64), default="not_verified")
    aadhaar_verification_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dob: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[list[UserRole]] = relationship(back_populates="user", cascade="all, delete-orphan")
    verifications: Mapped[list[UserVerification]] = relationship(back_populates="user")
    citizen: Mapped[Citizen | None] = relationship(back_populates="user", uselist=False)
    government_profile: Mapped[GovernmentUser | None] = relationship(back_populates="user", uselist=False)
    university: Mapped[University | None] = relationship(back_populates="user", uselist=False)
    industry: Mapped[Industry | None] = relationship(back_populates="user", uselist=False)


class UserRole(Base):
    __tablename__ = "user_roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    user: Mapped[User] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship()
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)


class UserVerification(Base, TimestampMixin):
    __tablename__ = "user_verifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32))  # email / mobile / admin
    code: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped[User] = relationship(back_populates="verifications")


class Citizen(Base, TimestampMixin):
    __tablename__ = "citizens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    district: Mapped[str] = mapped_column(String(128), default="")
    block: Mapped[str] = mapped_column(String(128), default="")
    village: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    user: Mapped[User] = relationship(back_populates="citizen")


class GovernmentDepartment(Base):
    __tablename__ = "government_departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class GovernmentUser(Base, TimestampMixin):
    __tablename__ = "government_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    official_id: Mapped[str] = mapped_column(String(128), default="")
    designation: Mapped[str] = mapped_column(String(255), default="")
    department_id: Mapped[int | None] = mapped_column(ForeignKey("government_departments.id"), nullable=True)
    district: Mapped[str] = mapped_column(String(128), default="")
    jurisdiction: Mapped[str] = mapped_column(String(255), default="")
    user: Mapped[User] = relationship(back_populates="government_profile")
    department: Mapped[GovernmentDepartment | None] = relationship()


class University(Base, TimestampMixin):
    __tablename__ = "universities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    institution_type: Mapped[str] = mapped_column(String(128), default="University")
    official_id: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    district: Mapped[str] = mapped_column(String(128), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    contact_person: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(32), default="")
    faculty_expertise: Mapped[str] = mapped_column(Text, default="")
    research_areas: Mapped[str] = mapped_column(Text, default="")
    laboratories: Mapped[str] = mapped_column(Text, default="")
    innovation_centre: Mapped[str] = mapped_column(Text, default="")
    incubation_centre: Mapped[str] = mapped_column(Text, default="")
    previous_projects: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[str] = mapped_column(String(64), default="pending_verification")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    state_id: Mapped[int | None] = mapped_column(ForeignKey("states.id"), nullable=True)
    institution_catalog_id: Mapped[int | None] = mapped_column(ForeignKey("institution_catalog.id"), nullable=True)
    user: Mapped[User] = relationship(back_populates="university")
    departments: Mapped[list[UniversityDepartment]] = relationship(back_populates="university", cascade="all, delete-orphan")
    documents: Mapped[list[UniversityDocument]] = relationship(back_populates="university", cascade="all, delete-orphan")
    faculty: Mapped[list[Faculty]] = relationship(back_populates="university")
    students: Mapped[list[Student]] = relationship(back_populates="university")


class UniversityDepartment(Base):
    __tablename__ = "university_departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    university: Mapped[University] = relationship(back_populates="departments")


class Faculty(Base, TimestampMixin):
    __tablename__ = "faculty"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(255), default="")
    expertise: Mapped[str] = mapped_column(Text, default="")
    university: Mapped[University] = relationship(back_populates="faculty")


class Student(Base, TimestampMixin):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(255), default="")
    enrollment_id: Mapped[str] = mapped_column(String(128), default="")
    university: Mapped[University] = relationship(back_populates="students")


class UniversityDocument(Base, TimestampMixin):
    __tablename__ = "university_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"), index=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    university: Mapped[University] = relationship(back_populates="documents")


class Industry(Base, TimestampMixin):
    __tablename__ = "industries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    organization_type: Mapped[str] = mapped_column(String(64), default="industry")
    sector: Mapped[str] = mapped_column(String(128), default="")
    registration_details: Mapped[str] = mapped_column(Text, default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    district: Mapped[str] = mapped_column(String(128), default="")
    contact_person: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(32), default="")
    technical_expertise: Mapped[str] = mapped_column(Text, default="")
    products_services: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[str] = mapped_column(Text, default="")
    csr_areas: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[str] = mapped_column(String(64), default="pending_verification")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped[User] = relationship(back_populates="industry")
    capabilities: Mapped[list[IndustryCapability]] = relationship(back_populates="industry", cascade="all, delete-orphan")
    documents: Mapped[list[IndustryDocument]] = relationship(back_populates="industry", cascade="all, delete-orphan")


class IndustryCapability(Base):
    __tablename__ = "industry_capabilities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    industry_id: Mapped[int] = mapped_column(ForeignKey("industries.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    industry: Mapped[Industry] = relationship(back_populates="capabilities")


class IndustryDocument(Base, TimestampMixin):
    __tablename__ = "industry_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    industry_id: Mapped[int] = mapped_column(ForeignKey("industries.id"), index=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    industry: Mapped[Industry] = relationship(back_populates="documents")


class ProblemCategory(Base):
    __tablename__ = "problem_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    subcategories: Mapped[str] = mapped_column(Text, default="")


class Problem(Base, TimestampMixin):
    __tablename__ = "problems"
    __table_args__ = (
        Index("ix_problems_status_district", "status", "district"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(128), index=True)
    subcategory: Mapped[str] = mapped_column(String(128), default="")
    expected_solution: Mapped[str] = mapped_column(Text, default="")
    affected_people_description: Mapped[str] = mapped_column(Text, default="")
    district: Mapped[str] = mapped_column(String(128), index=True)
    block: Mapped[str] = mapped_column(String(128), default="")
    village: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_affected_population: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    urgency: Mapped[str] = mapped_column(String(32), default="medium")
    frequency: Mapped[str] = mapped_column(String(64), default="")
    geographic_impact: Mapped[str] = mapped_column(String(64), default="village")
    existing_solution: Mapped[str] = mapped_column(Text, default="")
    current_government_action: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(64), default="pending_government_verification", index=True)
    assigned_department_id: Mapped[int | None] = mapped_column(ForeignKey("government_departments.id"), nullable=True)
    official_remarks: Mapped[str] = mapped_column(Text, default="")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    citizen: Mapped[User] = relationship(foreign_keys=[citizen_id])
    assigned_department: Mapped[GovernmentDepartment | None] = relationship()
    location: Mapped[ProblemLocation | None] = relationship(back_populates="problem", uselist=False)
    evidence: Mapped[list[ProblemEvidence]] = relationship(back_populates="problem")
    status_history: Mapped[list[ProblemStatusHistory]] = relationship(back_populates="problem")
    assignments: Mapped[list[ProblemAssignment]] = relationship(back_populates="problem")
    relations: Mapped[list[ProblemRelation]] = relationship(
        back_populates="problem", foreign_keys="ProblemRelation.problem_id"
    )


class ProblemLocation(Base):
    __tablename__ = "problem_locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), unique=True)
    district: Mapped[str] = mapped_column(String(128), default="")
    block: Mapped[str] = mapped_column(String(128), default="")
    village: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="map_selection")
    problem: Mapped[Problem] = relationship(back_populates="location")


class ProblemEvidence(Base, TimestampMixin):
    __tablename__ = "problem_evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    evidence_type: Mapped[str] = mapped_column(String(64))  # gps_location / additional_image / video / pdf / other
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    gps_from_image: Mapped[bool] = mapped_column(Boolean, default=False)
    problem: Mapped[Problem] = relationship(back_populates="evidence")
    stored_file: Mapped[StoredFile] = relationship()


class ProblemStatusHistory(Base, TimestampMixin):
    __tablename__ = "problem_status_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    previous_status: Mapped[str] = mapped_column(String(64), default="")
    new_status: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    problem: Mapped[Problem] = relationship(back_populates="status_history")


class ProblemAssignment(Base, TimestampMixin):
    __tablename__ = "problem_assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("government_departments.id"))
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    remarks: Mapped[str] = mapped_column(Text, default="")
    problem: Mapped[Problem] = relationship(back_populates="assignments")
    department: Mapped[GovernmentDepartment] = relationship()


class ProblemRelation(Base, TimestampMixin):
    __tablename__ = "problem_relations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    related_problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    relation_type: Mapped[str] = mapped_column(String(32), default="related")  # related / merged / separate
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    problem: Mapped[Problem] = relationship(back_populates="relations", foreign_keys=[problem_id])


class GovernmentAction(Base, TimestampMixin):
    __tablename__ = "government_actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(64))
    remarks: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[str] = mapped_column(Text, default="{}")


class GovernmentSolution(Base, TimestampMixin):
    __tablename__ = "government_solutions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), unique=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    versions: Mapped[list[GovernmentSolutionVersion]] = relationship(back_populates="solution")


class GovernmentSolutionVersion(Base, TimestampMixin):
    __tablename__ = "government_solution_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solution_id: Mapped[int] = mapped_column(ForeignKey("government_solutions.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, default="")
    action_taken: Mapped[str] = mapped_column(Text, default="")
    implementation_details: Mapped[str] = mapped_column(Text, default="")
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    attachments_json: Mapped[str] = mapped_column(Text, default="[]")
    solution: Mapped[GovernmentSolution] = relationship(back_populates="versions")


class AIAnalysis(Base, TimestampMixin):
    __tablename__ = "ai_analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    domain: Mapped[str] = mapped_column(String(128), default="")
    subdomain: Mapped[str] = mapped_column(String(128), default="")
    keywords: Mapped[str] = mapped_column(Text, default="")
    suggested_department: Mapped[str] = mapped_column(String(255), default="")
    classification_confidence: Mapped[float] = mapped_column(Float, default=0)
    priority_score: Mapped[float] = mapped_column(Float, default=0)
    priority_label: Mapped[str] = mapped_column(String(32), default="medium")
    priority_factors: Mapped[str] = mapped_column(Text, default="{}")
    remaining_requirements: Mapped[str] = mapped_column(Text, default="")
    required_skills: Mapped[str] = mapped_column(Text, default="")
    model_used: Mapped[str] = mapped_column(String(128), default="rule+tfidf")
    explanation: Mapped[str] = mapped_column(Text, default="")


class AIDuplicateMatch(Base, TimestampMixin):
    __tablename__ = "ai_duplicate_matches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    matched_problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    similarity: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text, default="")
    human_decision: Mapped[str] = mapped_column(String(32), default="pending")


class AIUniversityRecommendation(Base, TimestampMixin):
    __tablename__ = "ai_university_recommendations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"))
    matching_score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text, default="")
    relevant_department: Mapped[str] = mapped_column(String(255), default="")
    relevant_expertise: Mapped[str] = mapped_column(Text, default="")
    relevant_laboratory: Mapped[str] = mapped_column(Text, default="")
    relevant_previous_project: Mapped[str] = mapped_column(Text, default="")
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class UniversityReview(Base, TimestampMixin):
    __tablename__ = "university_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(64))  # review / clarification / no_opinion / suggestion
    note: Mapped[str] = mapped_column(Text, default="")


class UniversityOpinion(Base, TimestampMixin):
    __tablename__ = "university_opinions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    suggestion: Mapped[str] = mapped_column(Text, default="")
    recommended_improvement: Mapped[str] = mapped_column(Text, default="")
    technical_recommendation: Mapped[str] = mapped_column(Text, default="")
    alternative_solution: Mapped[str] = mapped_column(Text, default="")
    expected_benefit: Mapped[str] = mapped_column(Text, default="")
    government_decision: Mapped[str] = mapped_column(String(64), default="pending")
    government_remarks: Mapped[str] = mapped_column(Text, default="")
    attachments: Mapped[list[UniversityOpinionAttachment]] = relationship(back_populates="opinion")


class UniversityOpinionAttachment(Base, TimestampMixin):
    __tablename__ = "university_opinion_attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opinion_id: Mapped[int] = mapped_column(ForeignKey("university_opinions.id"), index=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    opinion: Mapped[UniversityOpinion] = relationship(back_populates="attachments")


class IndustryParticipation(Base, TimestampMixin):
    __tablename__ = "industry_participations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    industry_id: Mapped[int] = mapped_column(ForeignKey("industries.id"), index=True)
    participation_types: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(64), default="expressed_interest")


class IndustryProposal(Base, TimestampMixin):
    __tablename__ = "industry_proposals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participation_id: Mapped[int] = mapped_column(ForeignKey("industry_participations.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    industry_id: Mapped[int] = mapped_column(ForeignKey("industries.id"))
    proposal: Mapped[str] = mapped_column(Text, default="")
    technology_offered: Mapped[str] = mapped_column(Text, default="")
    resources: Mapped[str] = mapped_column(Text, default="")
    estimated_budget: Mapped[str] = mapped_column(String(64), default="")
    timeline: Mapped[str] = mapped_column(String(255), default="")
    team: Mapped[str] = mapped_column(Text, default="")
    expected_contribution: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(64), default="pending")
    review_remarks: Mapped[str] = mapped_column(Text, default="")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    university_id: Mapped[int | None] = mapped_column(ForeignKey("universities.id"), nullable=True)
    industry_id: Mapped[int | None] = mapped_column(ForeignKey("industries.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("government_departments.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    objectives: Mapped[str] = mapped_column(Text, default="")
    technology: Mapped[str] = mapped_column(Text, default="")
    budget: Mapped[str] = mapped_column(String(64), default="")
    timeline: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(64), default="active")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_outcome: Mapped[str] = mapped_column(Text, default="")
    members: Mapped[list[ProjectMember]] = relationship(back_populates="project")
    milestones: Mapped[list[ProjectMilestone]] = relationship(back_populates="project")
    documents: Mapped[list[ProjectDocument]] = relationship(back_populates="project")


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    member_type: Mapped[str] = mapped_column(String(32))  # faculty / student
    department: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(128), default="")
    responsibilities: Mapped[str] = mapped_column(Text, default="")
    project: Mapped[Project] = relationship(back_populates="members")


class ProjectMilestone(Base, TimestampMixin):
    __tablename__ = "project_milestones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    deadline: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    deliverable: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    comments: Mapped[str] = mapped_column(Text, default="")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    project: Mapped[Project] = relationship(back_populates="milestones")


class ProjectDocument(Base, TimestampMixin):
    __tablename__ = "project_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    project: Mapped[Project] = relationship(back_populates="documents")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int | None] = mapped_column(ForeignKey("problems.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text)
    is_announcement: Mapped[bool] = mapped_column(Boolean, default=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class MessageAttachment(Base, TimestampMixin):
    __tablename__ = "message_attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), index=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    recipient_role: Mapped[str] = mapped_column(String(64), default="")
    notification_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(String(64), default="")
    entity_id: Mapped[str] = mapped_column(String(64), default="")
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class ImpactMetric(Base, TimestampMixin):
    __tablename__ = "impact_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int | None] = mapped_column(ForeignKey("problems.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    people_benefited: Mapped[int] = mapped_column(Integer, default=0)
    geographic_coverage: Mapped[str] = mapped_column(String(255), default="")
    cost: Mapped[str] = mapped_column(String(64), default="")
    time_saved: Mapped[str] = mapped_column(String(128), default="")
    service_improvement: Mapped[str] = mapped_column(Text, default="")
    environmental_impact: Mapped[str] = mapped_column(Text, default="")
    technology_deployed: Mapped[str] = mapped_column(Text, default="")
    patents: Mapped[int] = mapped_column(Integer, default=0)
    publications: Mapped[int] = mapped_column(Integer, default=0)
    startups_created: Mapped[int] = mapped_column(Integer, default=0)
    technologies_transferred: Mapped[int] = mapped_column(Integer, default=0)
    before_text: Mapped[str] = mapped_column(Text, default="")
    solution_text: Mapped[str] = mapped_column(Text, default="")
    after_text: Mapped[str] = mapped_column(Text, default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class CitizenFeedback(Base, TimestampMixin):
    __tablename__ = "citizen_feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    satisfaction: Mapped[int] = mapped_column(Integer, default=3)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    comments: Mapped[str] = mapped_column(Text, default="")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(64), default="")
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), default="")
    previous_status: Mapped[str] = mapped_column(String(64), default="")
    new_status: Mapped[str] = mapped_column(String(64), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(String(255), default="")


class State(Base, TimestampMixin):
    __tablename__ = "states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    institutions: Mapped[list[InstitutionCatalog]] = relationship(back_populates="state", cascade="all, delete-orphan")


class InstitutionCatalog(Base, TimestampMixin):
    __tablename__ = "institution_catalog"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    short_name: Mapped[str] = mapped_column(String(64), default="")
    institution_type: Mapped[str] = mapped_column(String(128), default="University")
    official_website: Mapped[str] = mapped_column(String(255), default="")
    official_email: Mapped[str] = mapped_column(String(255), default="")
    district: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[str] = mapped_column(String(64), default="verified")
    status: Mapped[str] = mapped_column(String(32), default="active")
    state: Mapped[State] = relationship(back_populates="institutions")


class StoredFile(Base, TimestampMixin):
    __tablename__ = "stored_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(128))
    size: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="")
    entity_id: Mapped[str] = mapped_column(String(64), default="")
    storage_path: Mapped[str] = mapped_column(String(500))
    public: Mapped[bool] = mapped_column(Boolean, default=False)


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    problem_id: Mapped[int | None] = mapped_column(ForeignKey("problems.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text)
