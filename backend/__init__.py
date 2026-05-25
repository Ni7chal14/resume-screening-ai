"""
Package initialization for backend module
"""

__version__ = "1.0.0"
__author__ = "Resume Screening AI Team"

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Resume Screening AI Backend v{__version__} initialized")
