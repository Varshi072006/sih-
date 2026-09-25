from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class DuplicateDetectionService:
    def find_related(self, query: str, corpus: list[dict], threshold: float = 0.28) -> list[dict]:
        if not corpus:
            return []
        texts = [query] + [c["text"] for c in corpus]
        try:
            matrix = TfidfVectorizer(stop_words="english", min_df=1).fit_transform(texts)
        except ValueError:
            return []
        sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        results = []
        for item, score in zip(corpus, sims):
            if float(score) >= threshold:
                results.append(
                    {
                        "problem_id": item["id"],
                        "public_id": item.get("public_id"),
                        "title": item.get("title"),
                        "similarity": round(float(score), 3),
                        "reason": "Overlapping problem statement language detected by TF-IDF cosine similarity.",
                        "model_used": "sklearn_tfidf_cosine",
                    }
                )
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:8]


duplicate_detection_service = DuplicateDetectionService()
