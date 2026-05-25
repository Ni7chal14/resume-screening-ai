"""
Skill extraction from resumes and job descriptions.
"""

import logging
import json
import os
from typing import List, Set, Dict, Tuple
import re

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Extracts and categorizes skills from text."""
    
    def __init__(self, skills_file: str = None):
        """
        Initialize skill extractor with skills database.
        
        Args:
            skills_file: Path to skills JSON file. If None, uses default skills.
        """
        self.skills_db = self._load_skills(skills_file)
        self.all_skills = self._flatten_skills(self.skills_db)
        logger.info(f"Loaded {len(self.all_skills)} skills from database")
    
    @staticmethod
    def _load_skills(skills_file: str = None) -> Dict[str, List[str]]:
        """
        Load skills from JSON file.
        
        Args:
            skills_file: Path to skills JSON file.
            
        Returns:
            Dictionary of categorized skills.
        """
        try:
            if skills_file and os.path.exists(skills_file):
                with open(skills_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return default skills if file not found
                return SkillExtractor._get_default_skills()
        except Exception as e:
            logger.warning(f"Error loading skills file: {str(e)}. Using defaults.")
            return SkillExtractor._get_default_skills()
    
    @staticmethod
    def _get_default_skills() -> Dict[str, List[str]]:
        """
        Return default comprehensive skills database.
        
        Returns:
            Dictionary of categorized skills.
        """
        return {
            "Programming Languages": [
                "Python", "Java", "JavaScript", "C#", "C++", "Ruby", "Go", "Rust",
                "PHP", "Swift", "Kotlin", "TypeScript", "R", "MATLAB", "Scala", "Perl"
            ],
            "Web Frameworks": [
                "FastAPI", "Django", "Flask", "React", "Vue.js", "Angular", "Express.js",
                "Spring Boot", "ASP.NET", "Rails", "Laravel", "Next.js", "Nuxt.js"
            ],
            "Databases": [
                "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch",
                "Cassandra", "DynamoDB", "Firebase", "SQLite", "MariaDB",
                "Oracle", "SQL Server", "Neo4j", "CouchDB"
            ],
            "Cloud Platforms": [
                "AWS", "Azure", "Google Cloud", "GCP", "Kubernetes", "Docker",
                "Heroku", "DigitalOcean", "IBM Cloud", "Alibaba Cloud", "AWS Lambda"
            ],
            "DevOps & Tools": [
                "Git", "GitHub", "GitLab", "Jenkins", "Docker", "Kubernetes", "Terraform",
                "Ansible", "Prometheus", "Grafana", "ELK Stack", "GitHub Actions",
                "CircleCI", "Travis CI", "Apache Kafka", "RabbitMQ"
            ],
            "Data Science & ML": [
                "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn",
                "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "NLP", "Computer Vision",
                "Keras", "OpenCV", "NLTK", "SpaCy", "XGBoost"
            ],
            "Data Engineering": [
                "Apache Spark", "Hadoop", "Hive", "Presto", "Airflow", "Talend",
                "ETL", "Data Warehouse", "Data Lake", "Kafka", "Flink", "Dataflow"
            ],
            "APIs & Services": [
                "REST API", "GraphQL", "SOAP", "WebSocket", "OAuth", "JWT",
                "Microservices", "Message Queue", "gRPC", "OpenAPI", "Swagger"
            ],
            "Mobile Development": [
                "React Native", "Flutter", "Xamarin", "Swift", "Kotlin",
                "Android", "iOS", "Mobile App", "Cross-platform"
            ],
            "Testing & QA": [
                "Unit Testing", "Integration Testing", "Jest", "Pytest", "Selenium",
                "JUnit", "TestNG", "Cypress", "Mocha", "Chai", "QA", "Bug Tracking"
            ],
            "Soft Skills": [
                "Communication", "Leadership", "Project Management", "Problem Solving",
                "Teamwork", "Collaboration", "Agile", "Scrum", "Kanban", "Time Management",
                "Analytical Skills", "Critical Thinking"
            ]
        }
    
    @staticmethod
    def _flatten_skills(skills_db: Dict[str, List[str]]) -> List[str]:
        """
        Flatten skills database into single list.
        
        Args:
            skills_db: Categorized skills dictionary.
            
        Returns:
            Flat list of all skills.
        """
        flat_skills = []
        for category_skills in skills_db.values():
            flat_skills.extend(category_skills)
        return flat_skills
    
    def extract_skills(self, text: str, threshold: float = 0.6) -> List[str]:
        """
        Extract skills from text using fuzzy matching.
        
        Args:
            text: Input text to extract skills from.
            threshold: Minimum match confidence (0-1).
            
        Returns:
            List of extracted skills.
        """
        try:
            text_lower = text.lower()
            found_skills = set()
            
            # Direct matching
            for skill in self.all_skills:
                skill_lower = skill.lower()
                pattern = r'\b' + re.escape(skill_lower) + r'\b'

                if re.search(pattern, text_lower):
                    found_skills.add(skill)
            
            # Pattern-based matching for common variations
            skill_patterns = {
                'javascript': r'\bjs\b|\bjavascript\b',
                'python': r'\bpython\b',
                'java': r'\bjava\b(?!script)',
                'c#': r'c#|csharp',
                'c++': r'c\+\+',
                'react': r'\breact\b',
                'node': r'\bnode\.?js\b',
                'sql': r'\bsql\b',
                'html': r'\bhtml[45]?\b',
                'css': r'\bcss[3]?\b',
                'git': r'\bgit\b',
                'aws': r'\baws\b',
                'machine learning': r'\bml\b|\bmachine\s+learning\b',
            }
            
            for pattern_skill, pattern in skill_patterns.items():
                if re.search(pattern, text_lower):
                    found_skills.add(pattern_skill.title())
            
            logger.info(f"Extracted {len(found_skills)} skills from text")

            normalized_skills = {}
            display_skills = {}

            for skill in found_skills:

                key = skill.lower().strip()

                if key not in normalized_skills:
                    normalized_skills[key] = True
                    display_skills[key] = skill

            return sorted(display_skills.values())
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills based on skills database.
        
        Args:
            skills: List of skills to categorize.
            
        Returns:
            Dictionary of categorized skills.
        """
        try:
            categorized = {category: [] for category in self.skills_db}
            categorized['Other'] = []
            
            for skill in skills:
                found = False
                for category, category_skills in self.skills_db.items():
                    if any(s.lower() == skill.lower() for s in category_skills):
                        categorized[category].append(skill)
                        found = True
                        break
                
                if not found:
                    categorized['Other'].append(skill)
            
            # Remove empty categories
            categorized = {k: v for k, v in categorized.items() if v}
            logger.info(f"Categorized skills into {len(categorized)} categories")
            return categorized
        except Exception as e:
            logger.error(f"Error categorizing skills: {str(e)}")
            return {'Other': skills}
    
    def get_skill_categories(self) -> Dict[str, List[str]]:
        """
        Get all skill categories and their skills.
        
        Returns:
            Dictionary of all categories and skills.
        """
        return self.skills_db
    
    def search_skill(self, query: str) -> List[str]:
        """
        Search for skills matching query.
        
        Args:
            query: Search query.
            
        Returns:
            List of matching skills.
        """
        try:
            query_lower = query.lower()
            matches = [skill for skill in self.all_skills if query_lower in skill.lower()]
            logger.info(f"Found {len(matches)} skills matching '{query}'")
            return sorted(matches)
        except Exception as e:
            logger.error(f"Error searching skills: {str(e)}")
            return []
