SEVERITY_MAP = {"low": 1, "medium": 2, "high": 3, "critical": 4}
URGENCY_MAP = {"low": 1, "medium": 2, "high": 3, "immediate": 4}
GEO_MAP = {"household": 1, "village": 2, "block": 3, "district": 4, "state": 5}


class PriorityService:
    def recommend(
        self,
        affected_population: int,
        urgency: str,
        severity: str,
        evidence_count: int,
        geographic_impact: str,
        similar_reports: int,
    ) -> dict:
        pop = min(affected_population / 500, 4)
        urg = URGENCY_MAP.get((urgency or "medium").lower(), 2)
        sev = SEVERITY_MAP.get((severity or "medium").lower(), 2)
        ev = min(evidence_count, 4)
        geo = GEO_MAP.get((geographic_impact or "village").lower(), 2)
        sim = min(similar_reports, 4)
        score = (pop * 1.4) + (urg * 1.3) + (sev * 1.3) + (ev * 0.6) + (geo * 0.8) + (sim * 0.7)
        if score >= 14:
            label = "critical"
        elif score >= 10:
            label = "high"
        elif score >= 6:
            label = "medium"
        else:
            label = "low"
        return {
            "priority_score": round(score, 2),
            "priority_label": label,
            "factors": {
                "affected_population": affected_population,
                "urgency": urgency,
                "severity": severity,
                "evidence_quality": evidence_count,
                "geographic_impact": geographic_impact,
                "similar_reports": similar_reports,
            },
            "reason": "Weighted combination of population, urgency, severity, evidence, geography and similar reports.",
            "model_used": "weighted_priority_v1",
        }


priority_service = PriorityService()
