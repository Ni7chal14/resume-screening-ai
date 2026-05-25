"""
MongoDB Atlas database connection and operations.
"""

import logging
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from contextlib import contextmanager
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages MongoDB Atlas connections and operations."""
    
    def __init__(self, connection_string: str, database_name: str = "resume_screening", timeout: int = 5):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB Atlas connection string.
            database_name: Name of the database to use.
            timeout: Connection timeout in seconds.
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.timeout = timeout
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB Atlas."""
        try:
            logger.info("Connecting to MongoDB Atlas...")
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=self.timeout * 1000,
                connectTimeoutMS=self.timeout * 1000,
                retryWrites=True,
                w="majority"
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info(f"Connected to MongoDB database: {self.database_name}")
            self._ensure_collections()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {str(e)}")
            raise
    
    def _ensure_collections(self):
        """Ensure required collections exist with proper indexing."""
        try:
            collections_to_create = {
                'resumes': [
                    ('candidate_email', 1),
                    ('created_at', -1),
                ],
                'analyses': [
                    ('candidate_email', 1),
                    ('created_at', -1),
                    ('match_score', -1),
                ]
            }
            
            for collection_name, indexes in collections_to_create.items():
                if collection_name not in self.db.list_collection_names():
                    self.db.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")
                
                # Create indexes
                collection = self.db[collection_name]
                for index_field, direction in indexes:
                    try:
                        collection.create_index([(index_field, direction)])
                        logger.info(f"Created index on {collection_name}.{index_field}")
                    except Exception as e:
                        logger.warning(f"Index creation warning: {str(e)}")
        except Exception as e:
            logger.warning(f"Warning during collection setup: {str(e)}")
    
    def insert_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """
        Insert resume analysis into database.
        
        Args:
            analysis_data: Dictionary containing analysis results.
            
        Returns:
            Inserted document ID.
        """
        try:
            analysis_data['created_at'] = datetime.utcnow()
            analysis_data['updated_at'] = datetime.utcnow()
            
            result = self.db.analyses.insert_one(analysis_data)
            logger.info(f"Inserted analysis with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting analysis: {str(e)}")
            raise
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis by ID.
        
        Args:
            analysis_id: MongoDB document ID.
            
        Returns:
            Analysis document or None.
        """
        try:
            from bson.objectid import ObjectId
            result = self.db.analyses.find_one({'_id': ObjectId(analysis_id)})
            if result:
                result['_id'] = str(result['_id'])
            return result
        except Exception as e:
            logger.error(f"Error retrieving analysis: {str(e)}")
            return None
    
    def get_analyses_by_email(self, email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get all analyses for a candidate by email.
        
        Args:
            email: Candidate email address.
            limit: Maximum number of results to return.
            
        Returns:
            List of analysis documents.
        """
        try:
            analyses = list(
                self.db.analyses.find({'candidate_email': email})
                .sort('created_at', -1)
                .limit(limit)
            )
            for analysis in analyses:
                analysis['_id'] = str(analysis['_id'])
            return analyses
        except Exception as e:
            logger.error(f"Error retrieving analyses by email: {str(e)}")
            return []
    
    def get_top_matches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top matches by score.
        
        Args:
            limit: Maximum number of results to return.
            
        Returns:
            List of top matching analyses.
        """
        try:
            matches = list(
                self.db.analyses.find()
                .sort('match_score', -1)
                .limit(limit)
            )
            for match in matches:
                match['_id'] = str(match['_id'])
            return matches
        except Exception as e:
            logger.error(f"Error retrieving top matches: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics.
        """
        try:
            total_analyses = self.db.analyses.count_documents({})
            avg_match_score = list(
                self.db.analyses.aggregate([
                    {'$group': {
                        '_id': None,
                        'avg_score': {'$avg': '$match_score'},
                        'max_score': {'$max': '$match_score'},
                        'min_score': {'$min': '$match_score'}
                    }}
                ])
            )
            
            stats = {
                'total_analyses': total_analyses,
                'average_match_score': avg_match_score[0]['avg_score'] if avg_match_score else 0,
                'max_match_score': avg_match_score[0]['max_score'] if avg_match_score else 0,
                'min_match_score': avg_match_score[0]['min_score'] if avg_match_score else 0,
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def health_check(self) -> bool:
        """
        Check database connection health.
        
        Returns:
            True if connected, False otherwise.
        """
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
