"""
FastAPI backend for Resume Screening AI application.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, UploadFile, Form, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from backend.schemas import ResumeAnalysisRequest, ResumeAnalysisResponse, HealthCheck
from backend.resume_parser import ResumeParser
from backend.skill_extractor import SkillExtractor
from backend.similarity_engine import SimilarityEngine
from backend.database import MongoDBManager

from models.sentence_transformer import SimilarityModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
similarity_model = None
skill_extractor = None
similarity_engine = None
db_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global similarity_model, skill_extractor, similarity_engine, db_manager
    
    try:
        # Startup
        logger.info("Starting Resume Screening AI backend...")
        logger.info("DEPLOY TEST - TFIDF VERSION")
        
        # Initialize models
        logger.info("Loading Sentence Transformer model...")
        similarity_model = SimilarityModel()        

        logger.info("Loading skill extractor...")
        skills_file = os.path.join(os.path.dirname(__file__), '../data/skills.json')
        skill_extractor = SkillExtractor(skills_file=skills_file)
        
        logger.info("Initializing similarity engine...")
        similarity_engine = SimilarityEngine(similarity_model, skill_extractor)
        
        # Initialize database
        mongo_uri = os.getenv('MONGODB_URI')
        if not mongo_uri:
            logger.warning("MONGODB_URI not set. Database features will be unavailable.")
        else:
            logger.info("Connecting to MongoDB Atlas...")
            db_manager = MongoDBManager(connection_string=mongo_uri)
        
        logger.info("Backend started successfully")
        
        yield
        
        # Shutdown
        logger.info("Shutting down Resume Screening AI backend...")
        if db_manager:
            db_manager.close()
        logger.info("Backend shutdown complete")
    
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise


# Initialize FastAPI application
app = FastAPI(
    title="Resume Screening AI API",
    description="AI-powered resume screening and matching API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
origins = os.getenv('CORS_ORIGINS', 'http://localhost:8501,http://localhost:8000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    try:
        db_connected = db_manager.health_check() if db_manager else False
        
        return HealthCheck(
            status="healthy",
            version="1.0.0",
            database_connected=db_connected,
            model_loaded=similarity_model is not None
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            version="1.0.0",
            database_connected=False,
            model_loaded=False
        )


@app.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    candidate_name: Optional[str] = Form(None),
    candidate_email: Optional[str] = Form(None),
    position_title: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
) -> ResumeAnalysisResponse:
    """
    Analyze resume and compute match score with job description.
    
    Args:
        resume_file: PDF resume file.
        job_description: Job description text.
        candidate_name: Candidate name (optional).
        candidate_email: Candidate email (optional).
        position_title: Position title (optional).
        background_tasks: Background task queue.
        
    Returns:
        ResumeAnalysisResponse with match results.
    """
    try:
        # Validate inputs
        if not resume_file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        if not job_description or len(job_description.strip()) < 10:
            raise HTTPException(status_code=400, detail="Job description must be at least 10 characters")
        
        logger.info(f"Processing resume: {resume_file.filename}")
        
        # Read PDF
        pdf_content = await resume_file.read()
        
        # Extract text
        resume_text = ResumeParser.extract_text_from_pdf(pdf_content)
        is_valid, validation_msg = ResumeParser.validate_resume_content(resume_text)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_msg)
        
        # Clean text
        resume_text = ResumeParser.clean_text(resume_text)
        
        # Extract candidate info if not provided
        if not candidate_name:
            candidate_name = ResumeParser.extract_name(resume_text) or "Unknown"
        if not candidate_email:
            candidate_email = ResumeParser.extract_email(resume_text)
        
        logger.info(f"Candidate: {candidate_name} ({candidate_email or 'no email'})")
        
        # Compute match
        match_result = similarity_engine.compute_match(resume_text, job_description)
        
        logger.info(f"Match score: {match_result.match_score:.2f}")

        recommendations = []

        for skill in match_result.missing_skills:
            skill_name = (
                skill["skill"]
                if isinstance(skill, dict)
                else str(skill)
            )

            recommendations.append(
                f"Consider learning or adding experience with {skill_name}"
            )
        
        # Prepare response
        response = ResumeAnalysisResponse(
            match_score=match_result.match_score,
            matching_skills=match_result.matching_skills,
            missing_skills=match_result.missing_skills,
            resume_text=resume_text[:1000],  # Truncate for response
            job_description=job_description[:1000],
            recommendations=recommendations,
            analysis_timestamp=datetime.now()  # Will be set by pydantic
        )
        
        # Save to database in background
        if db_manager:
            async def save_analysis():
                try:
                    analysis_data = {
                        'candidate_name': candidate_name,
                        'candidate_email': candidate_email,
                        'position_title': position_title,
                        'match_score': match_result.match_score,
                        'matching_skills': match_result.matching_skills,
                        'missing_skills': match_result.missing_skills,
                        'resume_text': resume_text,
                        'job_description': job_description,
                    }
                    db_manager.insert_analysis(analysis_data)
                except Exception as e:
                    logger.error(f"Error saving analysis: {str(e)}")
            
            if background_tasks:
                background_tasks.add_task(save_analysis)
        
        return response
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/rank-resumes")
async def rank_resumes(
    resume_files: list[UploadFile] = File(...),
    job_description: str = Form(...)
):
    """
    Rank multiple resumes against one job description.
    """

    try:

        rankings = []

        for resume_file in resume_files:

            if not resume_file.filename.lower().endswith(".pdf"):
                continue

            pdf_content = await resume_file.read()

            resume_text = ResumeParser.extract_text_from_pdf(
                pdf_content
            )

            resume_text = ResumeParser.clean_text(
                resume_text
            )

            candidate_name = (
                ResumeParser.extract_name(
                    resume_text
                )
                or resume_file.filename
            )

            match_result = (
                similarity_engine.compute_match(
                    resume_text,
                    job_description
                )
            )

            rankings.append(
                {
                    "candidate_name":
                        candidate_name,

                    "filename":
                        resume_file.filename,

                    "score":
                        round(
                            match_result.match_score,
                            2
                        ),

                    "matching_skills":
                        len(
                            match_result.matching_skills
                        ),

                    "missing_skills":
                        len(
                            match_result.missing_skills
                        )
                }
            )

        rankings.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        for i, candidate in enumerate(
            rankings,
            start=1
        ):
            candidate["rank"] = i

        return {
            "total_candidates":
                len(rankings),

            "rankings":
                rankings
        }

    except Exception as e:

        logger.error(
            f"Ranking error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/analyze-text")
async def analyze_text(request: ResumeAnalysisRequest) -> ResumeAnalysisResponse:
    """
    Analyze resume from text (not file).
    
    Args:
        request: ResumeAnalysisRequest with resume and job description text.
        
    Returns:
        ResumeAnalysisResponse with match results.
    """
    try:
        logger.info("Processing text-based analysis")
        
        # Validate
        resume_text = ResumeParser.clean_text(request.resume_text)
        is_valid, validation_msg = ResumeParser.validate_resume_content(resume_text)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_msg)
        
        # Compute match
        match_result = similarity_engine.compute_match(resume_text, request.job_description)
        
        # Save to database
        if db_manager:
            try:
                analysis_data = {
                    'candidate_name': request.candidate_name or "Unknown",
                    'candidate_email': request.candidate_email,
                    'position_title': request.position_title,
                    'match_score': match_result.match_score,
                    'matching_skills': match_result.matching_skills,
                    'missing_skills': match_result.missing_skills,
                    'resume_text': resume_text,
                    'job_description': request.job_description,
                }
                db_manager.insert_analysis(analysis_data)
            except Exception as e:
                logger.warning(f"Error saving analysis: {str(e)}")
        
        recommendations = []

        for skill in match_result.missing_skills:

            skill_name = (
                skill["skill"]
                if isinstance(skill, dict)
                else str(skill)
            )

            recommendations.append(
                f"Consider learning or adding experience with {skill_name}"
            )

        return ResumeAnalysisResponse(
            match_score=match_result.match_score,
            matching_skills=match_result.matching_skills,
            missing_skills=match_result.missing_skills,
            resume_text=resume_text[:1000],
            job_description=request.job_description[:1000],
            recommendations=recommendations,
            analysis_timestamp=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/skills")
async def get_skills():
    """Get all available skill categories and skills."""
    try:
        skills = skill_extractor.get_skill_categories()
        return {"categories": skills}
    except Exception as e:
        logger.error(f"Error retrieving skills: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/skills/search")
async def search_skills(q: str = ""):
    """Search for skills by query."""
    try:
        if not q or len(q) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        results = skill_extractor.search_skill(q)
        return {"query": q, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching skills: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/statistics")
async def get_statistics():
    """Get database statistics."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        stats = db_manager.get_statistics()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/analyses/{email}")
async def get_candidate_analyses(email: str, limit: int = 10):
    """Get all analyses for a candidate."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        if limit < 1 or limit > 100:
            limit = 10
        
        analyses = db_manager.get_analyses_by_email(email, limit=limit)
        return {"email": email, "count": len(analyses), "analyses": analyses}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analyses: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/top-matches")
async def get_top_matches(limit: int = 10):
    """Get top matching resumes."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database not available")
        
        if limit < 1 or limit > 100:
            limit = 10
        
        matches = db_manager.get_top_matches(limit=limit)
        return {"count": len(matches), "matches": matches}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving top matches: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/all-scores")
async def get_all_scores():

    try:

        if not db_manager:
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )

        matches = db_manager.get_top_matches(
            limit=1000
        )

        names = [
            match.get(
                "candidate_name",
                "Unknown"
            )
            for match in matches
        ]

        scores = [
            match.get(
                "match_score",
                0
            )
            for match in matches
        ]

        return {
            "names": names,
            "scores": scores
        }

    except Exception as e:

        logger.error(
            f"Error retrieving scores: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Resume Screening AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "analyze_text": "/analyze-text",
            "skills": "/skills",
            "search_skills": "/skills/search",
            "statistics": "/statistics",
            "candidate_analyses": "/analyses/{email}",
            "top_matches": "/top-matches"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)