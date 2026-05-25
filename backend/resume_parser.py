"""
Resume parsing and text extraction from PDF files.
"""

import logging
import re
from typing import Optional, Tuple
import fitz  # PyMuPDF
import io

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parses PDF resumes and extracts text content."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_bytes: Binary content of PDF file.
            
        Returns:
            Extracted text from PDF.
            
        Raises:
            ValueError: If PDF is invalid or cannot be processed.
        """
        try:
            if not pdf_bytes:
                raise ValueError("PDF file is empty")
            
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            if pdf_document.page_count == 0:
                raise ValueError("PDF has no pages")
            
            text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                text += page_text + "\n"
            
            pdf_document.close()
            
            if not text.strip():
                raise ValueError("No text content found in PDF")
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text.
            
        Returns:
            Cleaned and normalized text.
        """
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove URLs
            text = re.sub(r'http\S+|www\S+', '', text)
            
            # Remove email addresses (optional, depending on needs)
            text = re.sub(r'\S+@\S+', '[EMAIL]', text)
            
            # Remove special characters but keep spaces and basic punctuation
            text = re.sub(r'[^\w\s.,;:\-()"]', '', text)
            
            # Remove extra spaces again after cleaning
            text = re.sub(r'\s+', ' ', text).strip()
            
            logger.info(f"Cleaned text to {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text
    
    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """
        Extract email address from resume text.
        
        Args:
            text: Resume text.
            
        Returns:
            Email address if found, None otherwise.
        """
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            match = re.search(email_pattern, text)
            if match:
                email = match.group()
                logger.info(f"Found email: {email}")
                return email
            return None
        except Exception as e:
            logger.warning(f"Error extracting email: {str(e)}")
            return None
    
    @staticmethod
    def extract_name(text: str) -> Optional[str]:
        """
        Extract candidate name from resume (usually at the beginning).
        
        Args:
            text: Resume text.
            
        Returns:
            Candidate name if found, None otherwise.
        """
        try:
            # Split by lines and get the first substantial line
            lines = text.split('\n')
            for line in lines:
                cleaned = line.strip()
                # Skip if too short or contains email/numbers
                if len(cleaned) > 2 and len(cleaned) < 100 and '@' not in cleaned:
                    # Check if line contains mostly letters and spaces
                    if sum(c.isalpha() or c.isspace() for c in cleaned) > len(cleaned) * 0.7:
                        logger.info(f"Extracted name: {cleaned}")
                        return cleaned
            return None
        except Exception as e:
            logger.warning(f"Error extracting name: {str(e)}")
            return None
    
    @staticmethod
    def validate_resume_content(text: str, min_length: int = 50) -> Tuple[bool, str]:
        """
        Validate if extracted text is a valid resume.
        
        Args:
            text: Extracted text.
            min_length: Minimum acceptable text length.
            
        Returns:
            Tuple of (is_valid, message).
        """
        try:
            if not text or len(text.strip()) < min_length:
                return False, f"Resume text is too short (minimum {min_length} characters required)"
            
            # Check for common resume keywords
            resume_keywords = ['experience', 'education', 'skill', 'work', 'project', 'certification']
            text_lower = text.lower()
            found_keywords = sum(1 for kw in resume_keywords if kw in text_lower)
            
            if found_keywords == 0:
                logger.warning("No common resume keywords found")
                return False, "Resume content does not appear to contain typical resume sections"
            
            logger.info(f"Resume validation passed with {found_keywords} keywords found")
            return True, "Resume content is valid"
        except Exception as e:
            logger.error(f"Error validating resume: {str(e)}")
            return False, f"Error validating resume: {str(e)}"
