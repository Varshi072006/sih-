ROLES = [
    "citizen",
    "university",
    "faculty",
    "student",
    "industry",
    "startup",
    "msme",
    "csr",
    "government_officer",
    "government_department",
    "admin",
    "super_admin",
]

GOVERNMENT_ROLES = {"government_officer", "government_department", "admin", "super_admin"}
ADMIN_ROLES = {"admin", "super_admin"}
UNIVERSITY_ROLES = {"university", "faculty", "student"}
INDUSTRY_ROLES = {"industry", "startup", "msme", "csr"}

STATUS = {
    "submitted": "submitted",
    "pending_government_verification": "pending_government_verification",
    "verified": "verified",
    "rejected": "rejected",
    "assigned_to_department": "assigned_to_department",
    "under_department_review": "under_department_review",
    "action_solution_uploaded": "action_solution_uploaded",
    "ai_university_analysis": "ai_university_analysis",
    "universities_notified": "universities_notified",
    "university_review": "university_review",
    "university_opinion_submitted": "university_opinion_submitted",
    "no_opinion": "no_opinion",
    "government_review": "government_review",
    "solution_updated": "solution_updated",
    "done_solution": "done_solution",
    "industry_participation": "industry_participation",
    "implementation_pilot": "implementation_pilot",
    "completed": "completed",
}

STATUS_LABELS = {
    "submitted": "Submitted",
    "pending_government_verification": "Pending Government Verification",
    "verified": "Verified",
    "rejected": "Rejected",
    "assigned_to_department": "Assigned to Department",
    "under_department_review": "Under Department Review",
    "action_solution_uploaded": "Action/Solution Uploaded",
    "ai_university_analysis": "AI University Analysis",
    "universities_notified": "Universities Notified",
    "university_review": "University Review",
    "university_opinion_submitted": "University Opinion Submitted",
    "no_opinion": "No Opinion",
    "government_review": "Government Review",
    "solution_updated": "Solution Updated",
    "done_solution": "Done Solution",
    "industry_participation": "Industry Participation",
    "implementation_pilot": "Implementation/Pilot",
    "completed": "Completed",
}

ALLOWED_TRANSITIONS = {
    "submitted": ["pending_government_verification"],
    "pending_government_verification": ["verified", "rejected"],
    "verified": ["assigned_to_department", "rejected"],
    "rejected": [],
    "assigned_to_department": ["under_department_review"],
    "under_department_review": ["action_solution_uploaded"],
    "action_solution_uploaded": ["ai_university_analysis"],
    "ai_university_analysis": ["universities_notified"],
    "universities_notified": ["university_review"],
    "university_review": ["university_opinion_submitted", "no_opinion", "government_review"],
    "university_opinion_submitted": ["government_review"],
    "no_opinion": ["government_review", "done_solution"],
    "government_review": ["solution_updated", "done_solution"],
    "solution_updated": ["done_solution", "government_review"],
    "done_solution": ["industry_participation", "implementation_pilot", "completed"],
    "industry_participation": ["implementation_pilot", "completed"],
    "implementation_pilot": ["completed"],
    "completed": [],
}

CATEGORIES = {
    "Education": ["School Infrastructure", "Attendance", "Digital Learning", "Teacher Shortage"],
    "Healthcare": ["Primary Care Access", "Maternal Health", "Diagnostics", "Ambulance"],
    "Agriculture": ["Crop Disease", "Irrigation", "Market Access", "Soil Health"],
    "Water Management": ["Drinking Water Quality", "Supply Shortage", "Contamination", "Irrigation Water"],
    "Sanitation": ["Toilets", "Drainage", "Open Defecation"],
    "Environment": ["Air Quality", "Forest Degradation", "Mining Impact"],
    "Energy": ["Rural Electrification", "Solar", "Unreliable Supply"],
    "Rural Livelihoods": ["Employment", "Skill Development", "SHG Support"],
    "Accessibility": ["Disability Access", "Transport Access"],
    "Urban Infrastructure": ["Roads", "Street Lighting", "Waste", "Housing"],
    "Public Administration": ["Service Delivery", "Documentation", "Grievance"],
    "Other": ["Other"],
}

DEPARTMENT_MAP = {
    "Water Management": "Water Resources / Rural Water Supply",
    "Urban Infrastructure": "Rural Development / Urban Local Body",
    "Education": "Education Department",
    "Healthcare": "Health Department",
    "Agriculture": "Agriculture Department",
    "Sanitation": "Panchayati Raj / Urban Local Body",
    "Environment": "Forest, Environment & Climate Change",
    "Energy": "Energy Department",
    "Rural Livelihoods": "Rural Development",
    "Accessibility": "Social Welfare",
    "Public Administration": "Department of Personnel / District Administration",
    "Other": "District Administration",
}

JHARKHAND_DISTRICTS = [
    "Ranchi",
    "Dhanbad",
    "Bokaro",
    "East Singhbhum",
    "West Singhbhum",
    "Hazaribagh",
    "Giridih",
    "Deoghar",
    "Dumka",
    "Palamu",
    "Garhwa",
    "Latehar",
    "Chatra",
    "Koderma",
    "Ramgarh",
    "Gumla",
    "Simdega",
    "Khunti",
    "Lohardaga",
    "Pakur",
    "Godda",
    "Sahebganj",
    "Jamtara",
    "Saraikela-Kharsawan",
]

ALLOWED_MIME = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "video/mp4": [".mp4"],
    "application/pdf": [".pdf"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
}

INDUSTRY_PARTICIPATION_TYPES = [
    "Mentorship",
    "Funding",
    "Technology",
    "Prototype",
    "Testing",
    "Infrastructure",
    "Deployment",
    "CSR Support",
    "Technology Transfer",
    "Co-development",
]

MILESTONE_NAMES = [
    "Research",
    "Design",
    "Development",
    "Prototype",
    "Testing",
    "Pilot",
    "Deployment",
]
