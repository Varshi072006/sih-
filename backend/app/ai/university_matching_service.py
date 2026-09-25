from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class UniversityMatchingService:
    def match(self, problem_text: str, universities: list[dict], top_n: int = 5) -> list[dict]:
        if not universities:
            return []
        profiles = []
        for u in universities:
            profiles.append(
                " ".join(
                    [
                        u.get("name", ""),
                        u.get("departments", ""),
                        u.get("faculty_expertise", ""),
                        u.get("research_areas", ""),
                        u.get("laboratories", ""),
                        u.get("previous_projects", ""),
                        u.get("technologies", ""),
                    ]
                )
            )
        texts = [problem_text] + profiles
        try:
            matrix = TfidfVectorizer(stop_words="english").fit_transform(texts)
        except ValueError:
            return []
        sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        ranked = []
        for u, score in zip(universities, sims):
            ranked.append(
                {
                    "university_id": u["id"],
                    "name": u.get("name"),
                    "matching_score": round(float(score) * 100, 1),
                    "reason": self._reason(u, problem_text),
                    "relevant_department": (u.get("departments") or "").split(",")[0].strip(),
                    "relevant_expertise": (u.get("faculty_expertise") or "")[:240],
                    "relevant_laboratory": (u.get("laboratories") or "")[:240],
                    "relevant_previous_project": (u.get("previous_projects") or "")[:240],
                    "model_used": "tfidf_weighted_matching_v1",
                }
            )
        ranked.sort(key=lambda x: x["matching_score"], reverse=True)
        return ranked[:top_n]

    def _reason(self, uni: dict, problem_text: str) -> str:
        bits = []
        hay = f"{uni.get('departments','')} {uni.get('research_areas','')} {uni.get('laboratories','')}".lower()
        for token in ["water", "civil", "agriculture", "health", "energy", "road", "iot", "environment"]:
            if token in problem_text.lower() and token in hay:
                bits.append(f"Overlap on {token} expertise")
        if uni.get("laboratories"):
            bits.append("Laboratory capability listed")
        if uni.get("previous_projects"):
            bits.append("Prior related projects")
        return "; ".join(bits) or "Profile similarity to problem statement and government solution."


university_matching_service = UniversityMatchingService()
