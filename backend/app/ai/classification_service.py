"""Keyword/rule classification with optional sklearn TF-IDF similarity.

Sentence-Transformers can replace the vector backend without changing callers.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from app.utils.constants import CATEGORIES, DEPARTMENT_MAP

KEYWORD_MAP = {
    "Water Management": [
        "water",
        "drinking",
        "contamination",
        "well",
        "handpump",
        "arsenic",
        "fluoride",
        "pipeline",
        "borewell",
    ],
    "Healthcare": ["health", "hospital", "phc", "clinic", "doctor", "ambulance", "maternal", "vaccine"],
    "Education": ["school", "teacher", "attendance", "classroom", "student", "dropout"],
    "Agriculture": ["crop", "farm", "paddy", "disease", "pest", "irrigation", "soil", "fertilizer"],
    "Sanitation": ["toilet", "drainage", "sewage", "open defecation", "latrine"],
    "Environment": ["forest", "pollution", "mining", "air quality", "wildlife"],
    "Energy": ["electricity", "solar", "power", "transformer", "outage"],
    "Urban Infrastructure": ["road", "pothole", "street light", "waste", "garbage", "housing"],
    "Rural Livelihoods": ["livelihood", "employment", "shg", "skill", "income"],
    "Accessibility": ["disability", "ramp", "accessible", "wheelchair"],
    "Public Administration": ["certificate", "ration", "aadhaar", "office", "delay"],
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]{3,}", (text or "").lower())


class ClassificationService:
    def classify(self, title: str, description: str, category_hint: str = "") -> dict:
        text = f"{title} {description}".lower()
        scores = {}
        for cat, words in KEYWORD_MAP.items():
            scores[cat] = sum(1 for w in words if w in text)
        best = max(scores, key=scores.get) if scores else "Other"
        if scores.get(best, 0) == 0 and category_hint in CATEGORIES:
            best = category_hint
        confidence = min(0.95, 0.45 + 0.1 * scores.get(best, 0))
        tokens = _tokens(text)
        common = [w for w, _ in Counter(tokens).most_common(8)]
        subs = CATEGORIES.get(best, ["Other"])
        subdomain = subs[0]
        for s in subs:
            if s.lower().split()[0] in text:
                subdomain = s
                break
        return {
            "domain": best,
            "subdomain": subdomain,
            "keywords": common,
            "suggested_department": DEPARTMENT_MAP.get(best, "District Administration"),
            "confidence": round(confidence, 2),
            "model_used": "keyword_classifier_v1",
            "reason": f"Keyword overlap with {best} domain terms.",
        }


classification_service = ClassificationService()
