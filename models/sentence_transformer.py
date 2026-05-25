"""
Lightweight TF-IDF Similarity Model
"""

import logging
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SimilarityModel:

    def __init__(self):
        logger.info("Using TF-IDF Similarity Model")

    def compute_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:

        try:

            vectorizer = TfidfVectorizer()

            vectors = vectorizer.fit_transform(
                [text1, text2]
            )

            similarity = cosine_similarity(
                vectors[0],
                vectors[1]
            )[0][0]

            return float(
                max(
                    0.0,
                    min(
                        1.0,
                        similarity
                    )
                )
            )

        except Exception as e:

            logger.error(
                f"Similarity error: {str(e)}"
            )

            return 0.0

    def compute_batch_similarity(
        self,
        queries: List[str],
        corpus: List[str]
    ) -> Tuple[List[int], List[float]]:

        top_indices = []
        top_scores = []

        for query in queries:

            best_score = 0
            best_index = -1

            for i, item in enumerate(corpus):

                score = self.compute_similarity(
                    query,
                    item
                )

                if score > best_score:
                    best_score = score
                    best_index = i

            top_indices.append(best_index)
            top_scores.append(best_score)

        return top_indices, top_scores