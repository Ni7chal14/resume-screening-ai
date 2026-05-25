"""
Similarity computation engine for resume and job description matching.
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Data class for match results."""
    match_score: float
    matching_skills: List[Dict[str, any]]
    missing_skills: List[Dict[str, any]]
    resume_summary: str
    job_requirements_summary: str


class SimilarityEngine:
    """ Computes similarity between resumes and job descriptions."""
    
    def __init__(self, similarity_model, skill_extractor):
        """
        Initialize similarity engine.
        
        Args:
            similarity_model: Sentence transformer model for embeddings.
            skill_extractor: Skill extractor instance.
        """
        self.similarity_model = similarity_model
        self.skill_extractor = skill_extractor
    
    def compute_match(
        self,
        resume_text: str,
        job_description: str,
        skill_threshold: float = 0.5
    ) -> MatchResult:
        """
        Compute comprehensive match between resume and job description.
        
        Args:
            resume_text: Extracted resume text.
            job_description: Job description text.
            skill_threshold: Minimum similarity score for skill matching.
            
        Returns:
            MatchResult object with scores and skills.
        """
        try:
            logger.info("Computing match between resume and job description")
            
            # Extract skills from both texts
            resume_skills = self.skill_extractor.extract_skills(resume_text)
            job_skills = self.skill_extractor.extract_skills(job_description)
            
            logger.info(f"Resume skills: {len(resume_skills)}, Job skills: {len(job_skills)}")
            
            # Compute overall semantic similarity
            overall_similarity = self.similarity_model.compute_similarity(
                resume_text, job_description
            )

            overall_similarity = max(
                0.0,
                min(
                    1.0,
                    float(overall_similarity)
                )
            )
            logger.info(f"Overall similarity: {overall_similarity:.4f}")
            
            # Match skills with similarity scores
            matching_skills, missing_skills = self._match_skills(
                resume_skills, job_skills, skill_threshold
            )
            
            # Calculate final match score
            match_score = self._calculate_match_score(
                overall_similarity=overall_similarity,
                matching_skills=matching_skills,
                missing_skills=missing_skills,
                job_skills=job_skills
            )
            
            # Generate summaries
            resume_summary = self._generate_summary(resume_text, resume_skills)
            job_summary = self._generate_summary(job_description, job_skills)
            
            logger.info(f"Final match score: {match_score:.2f}")
            
            return MatchResult(
                match_score=match_score,
                matching_skills=matching_skills,
                missing_skills=missing_skills,
                resume_summary=resume_summary,
                job_requirements_summary=job_summary
            )
        except Exception as e:
            logger.error(f"Error computing match: {str(e)}")
            raise
    
    def _match_skills(
        self,
        resume_skills,
        job_skills,
        threshold
    ):

        try:

            matching_skills = []
            missing_skills = []

            for job_skill in job_skills:

                best_score = 0
                best_match = None

                for resume_skill in resume_skills:

                    score = self.similarity_model.compute_similarity(
                        job_skill,
                        resume_skill
                    )

                    if score > best_score:

                        best_score = score
                        best_match = resume_skill

                if best_score >= threshold:

                    matching_skills.append({
                        "skill": job_skill,
                        "matched_skill": best_match,
                        "similarity_score": float(best_score)
                    })

                else:

                    missing_skills.append({
                        "skill": job_skill,
                        "matched_skill": None,
                        "similarity_score": float(best_score)
                    })

            matching_skills.sort(
                key=lambda x: x["similarity_score"],
                reverse=True
            )

            missing_skills.sort(
                key=lambda x: x["similarity_score"],
                reverse=True
            )

            return matching_skills, missing_skills

        except Exception as e:

            logger.error(
                f"Error matching skills: {str(e)}"
            )

            return [], []
    
    def _calculate_match_score(
        self,
        overall_similarity: float,
        matching_skills: List[Dict],
        missing_skills: List[Dict],
        job_skills: List[str]
    ) -> float:
        """
        Calculate final match score (0-100).
        
        Args:
            overall_similarity: Overall semantic similarity (0-1).
            matching_skills: List of matched skills.
            missing_skills: List of missing skills.
            job_skills: Total job requirements.
            
        Returns:
            Match score between 0 and 100.
        """
        try:
            if not job_skills:
                return overall_similarity * 100
            
            # Calculate skill coverage
            matched_count = len(matching_skills)
            total_count = len(job_skills)
            skill_coverage = matched_count / total_count if total_count > 0 else 0
            
            # Calculate average skill similarity for matched skills
            if matching_skills:
                avg_skill_similarity = sum(s['similarity_score'] for s in matching_skills) / len(matching_skills)
            else:
                avg_skill_similarity = 0
            
            # Weighted calculation
            # 40% overall semantic similarity + 40% skill coverage + 20% average skill similarity
            match_score = (
                overall_similarity * 0.2 +
                skill_coverage * 0.5 +
                avg_skill_similarity * 0.3
            ) * 100
            
            # Clamp to 0-100
            match_score = max(0, min(100, match_score))
            
            logger.info(
                f"Match score calculation: "
                f"semantic={overall_similarity:.2f}, "
                f"coverage={skill_coverage:.2f}, "
                f"avg_similarity={avg_skill_similarity:.2f}, "
                f"final={match_score:.2f}"
            )
            
            return float(match_score)
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return 0.0
    
    def _generate_summary(self, text: str, skills: List[str]) -> str:
        """
        Generate text summary.
        
        Args:
            text: Input text.
            skills: Extracted skills.
            
        Returns:
            Summary string.
        """
        try:
            # Get first meaningful sentence(s)
            sentences = text.split('.')
            summary_parts = []
            
            for sentence in sentences[:3]:
                cleaned = sentence.strip()
                if len(cleaned) > 20:
                    summary_parts.append(cleaned)
            
            summary = '. '.join(summary_parts)[:200]
            
            if skills:
                summary += f"\n\nKey Skills: {', '.join(skills[:5])}"
            
            return summary
        except Exception as e:
            logger.warning(f"Error generating summary: {str(e)}")
            return ""
