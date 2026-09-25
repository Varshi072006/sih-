from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    verification_status: str
    full_name: str
    user_id: int


class LoginIn(BaseModel):
    email: str
    password: str


class VerifyIn(BaseModel):
    email: EmailStr
    code: str


class CitizenRegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    mobile: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8)
    confirm_password: str
    district: str
    block: str = ""
    village: str = ""
    address: str = ""


class UniversityRegisterIn(BaseModel):
    name: str
    institution_type: str = "University"
    official_id: str = ""
    address: str = ""
    district: str
    website: str = ""
    contact_person: str = Field(min_length=2)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8)
    departments: str = Field(min_length=1)
    faculty_expertise: str = Field(min_length=1)
    research_areas: str = Field(min_length=1)
    laboratories: str = Field(min_length=1)
    innovation_centre: str = Field(min_length=1)
    incubation_centre: str = Field(min_length=1)
    previous_projects: str = Field(min_length=1)
    technologies: str = Field(min_length=1)


class IndustryRegisterIn(BaseModel):
    company_name: str
    organization_type: str = "industry"
    sector: str = ""
    registration_details: str = ""
    website: str = ""
    address: str = ""
    district: str
    contact_person: str
    email: EmailStr
    phone: str
    password: str = Field(min_length=8)
    technical_expertise: str = ""
    products_services: str = ""
    technologies: str = ""
    csr_areas: str = ""
    funding_capability: bool = False
    mentorship_capability: bool = False
    prototype_capability: bool = False
    testing_capability: bool = False
    deployment_capability: bool = False


class GovernmentRegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    official_id: str
    designation: str = ""
    department_code: str = ""
    district: str = ""
    jurisdiction: str = ""
    mobile: str = ""


class ProblemCreateIn(BaseModel):
    title: str = Field(min_length=8, max_length=300)
    description: str = Field(min_length=20)
    category: str
    subcategory: str = ""
    expected_solution: str = ""
    affected_people_description: str = ""
    district: str
    block: str = ""
    village: str = ""
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    location_source: str = "map_selection"
    estimated_affected_population: int = 0
    severity: str = "medium"
    urgency: str = "medium"
    frequency: str = ""
    geographic_impact: str = "village"
    existing_solution: str = ""
    current_government_action: str = ""


class RemarksIn(BaseModel):
    remarks: str = ""


class AssignIn(BaseModel):
    department_id: int
    remarks: str = ""


class DuplicateDecisionIn(BaseModel):
    related_problem_id: int
    decision: str
    reason: str = ""


class SolutionIn(BaseModel):
    description: str
    action_taken: str
    implementation_details: str = ""


class OpinionIn(BaseModel):
    suggestion: str
    recommended_improvement: str = ""
    technical_recommendation: str = ""
    alternative_solution: str = ""
    expected_benefit: str = ""


class OpinionReviewIn(BaseModel):
    decision: str
    remarks: str = ""
    update_solution: bool = False
    solution: SolutionIn | None = None


class UniversitySelectIn(BaseModel):
    university_ids: list[int]


class ParticipateIn(BaseModel):
    participation_types: list[str]


class ProposalIn(BaseModel):
    proposal: str
    technology_offered: str = ""
    resources: str = ""
    estimated_budget: str = ""
    timeline: str = ""
    team: str = ""
    expected_contribution: str = ""


class ProjectCreateIn(BaseModel):
    problem_id: int
    university_id: int | None = None
    industry_id: int | None = None
    title: str
    objectives: str = ""
    technology: str = ""
    budget: str = ""
    timeline: str = ""


class TeamMemberIn(BaseModel):
    name: str
    member_type: str
    department: str = ""
    role: str = ""
    responsibilities: str = ""


class MilestoneUpdateIn(BaseModel):
    status: str | None = None
    comments: str | None = None
    deadline: str | None = None
    description: str | None = None
    deliverable: str | None = None
    approved: bool | None = None


class MessageIn(BaseModel):
    recipient_id: int
    subject: str = ""
    body: str
    problem_id: int | None = None
    project_id: int | None = None


class FeedbackIn(BaseModel):
    satisfaction: int = Field(ge=1, le=5)
    resolved: bool = False
    comments: str = ""


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    primary_role: str
    verification_status: str
    is_demo: bool
    mobile: str = ""

    class Config:
        from_attributes = True
