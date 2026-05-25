"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SkillMatch(BaseModel):
    """Model for individual skill match."""
    skill: str
    similarity_score: float = Field(..., ge=0, le=1)
    matched_skill: str | None = None

class ResumeAnalysisRequest(BaseModel):
    """Model for resume analysis request."""
    resume_text: str = Field(..., min_length=10)
    job_description: str = Field(..., min_length=10)
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    position_title: Optional[str] = None


class ResumeAnalysisResponse(BaseModel):
    """Model for resume analysis response."""
    match_score: float = Field(..., ge=0, le=100)
    matching_skills: List[SkillMatch]
    missing_skills: List[SkillMatch]
    resume_text: str
    job_description: str
    recommendations: list[str]
    analysis_timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "match_score": 75.5,
                "matching_skills": [
                    {"skill": "Python", "similarity_score": 0.95, "matched": True},
                    {"skill": "FastAPI", "similarity_score": 0.88, "matched": True}
                ],
                "missing_skills": [
                    {"skill": "Kubernetes", "similarity_score": 0.45, "matched": False}
                ],
                "resume_text": "...",
                "job_description": "...",
                "analysis_timestamp": "2024-01-01T12:00:00"
            }
        }


class ResumeDocument(BaseModel):
    """Model for storing resume analysis in database."""
    candidate_name: str
    candidate_email: Optional[str] = None
    position_title: Optional[str] = None
    match_score: float
    matching_skills: List[dict]
    missing_skills: List[dict]
    resume_text: str
    job_description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    version: str
    database_connected: bool
    model_loaded: bool
