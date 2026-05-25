"""
Sentence Transformer Model Handler for Semantic Similarity
"""

import logging
from typing import List, Tuple
from sentence_transformers import SentenceTransformer, util
import torch

logger = logging.getLogger(__name__)


class SimilarityModel:
    """Handles semantic similarity computations using Sentence Transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Sentence Transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use.
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading model {model_name} on device {self.device}")
        self.model = SentenceTransformer(model_name, device=self.device)
        
    def encode(self, texts: List[str]) -> List:
        """
        Encode texts to embeddings.
        
        Args:
            texts: List of text strings to encode.
            
        Returns:
            List of embeddings.
        """
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=True)
            logger.info(f"Encoded {len(texts)} texts to embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            raise
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text string.
            text2: Second text string.
            
        Returns:
            Similarity score between 0 and 1.
        """
        try:
            embeddings = self.encode([text1, text2])
            similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1])
            score = similarity.item()
            logger.info(f"Similarity computed: {score:.4f}")
            return float(score)
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            raise
    
    def compute_batch_similarity(self, queries: List[str], corpus: List[str]) -> Tuple[List[int], List[float]]:
        """
        Compute similarity between queries and corpus (returns top match indices and scores).
        
        Args:
            queries: List of query texts.
            corpus: List of corpus texts.
            
        Returns:
            Tuple of (top_match_indices, top_match_scores).
        """
        try:
            query_embeddings = self.encode(queries)
            corpus_embeddings = self.encode(corpus)
            
            hits = util.semantic_search(query_embeddings, corpus_embeddings, top_k=1)
            
            top_indices = []
            top_scores = []
            
            for hit in hits:
                if hit:
                    top_indices.append(hit[0]['corpus_id'])
                    top_scores.append(hit[0]['score'])
                else:
                    top_indices.append(-1)
                    top_scores.append(0.0)
            
            logger.info(f"Batch similarity computed for {len(queries)} queries")
            return top_indices, top_scores
        except Exception as e:
            logger.error(f"Error computing batch similarity: {str(e)}")
            raise
    
    def extract_skills_similarity(self, text: str, skills: List[str]) -> List[Tuple[str, float]]:
        """
        Extract skills from text and return with similarity scores.
        
        Args:
            text: Resume or document text.
            skills: List of skills to search for.
            
        Returns:
            List of tuples (skill, similarity_score) sorted by score.
        """
        try:
            text_embedding = self.encode([text])[0]
            skill_embeddings = self.encode(skills)
            
            similarities = util.pytorch_cos_sim(text_embedding, skill_embeddings)[0]
            
            results = [(skill, score.item()) for skill, score in zip(skills, similarities)]
            results = sorted(results, key=lambda x: x[1], reverse=True)
            
            logger.info(f"Extracted {len(results)} skills with similarity scores")
            return results
        except Exception as e:
            logger.error(f"Error extracting skills similarity: {str(e)}")
            raise