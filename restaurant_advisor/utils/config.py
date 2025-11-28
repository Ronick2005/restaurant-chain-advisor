import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DATABASE", "restaurant_advisor")  # For consistency with imports
MONGODB_DATABASE = MONGODB_DB_NAME  # Keep original for backwards compatibility
MONGODB_COLLECTION = "documents"
MONGODB_VECTOR_COLLECTION = "vectors"

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LangSmith configuration
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "restaurant-advisor")

# JWT Secret for authentication
JWT_SECRET = os.getenv("JWT_SECRET", "default-secret-key-change-in-production")

# User Agent for web scraping
USER_AGENT = os.getenv("USER_AGENT", "RestaurantAdvisorBot/1.0")

# Access control roles and permissions
ROLES = {
    "admin": {
        "kb_access": ["read", "write", "delete"],
        "kg_access": ["read", "write", "delete"],
        "agent_access": ["all"],
        "domain_access": ["all"],
        "user_management": True,
        "data_sources_access": ["all"],
        "memory_access": ["read", "write", "delete"],
        "description": "Full access to all system capabilities"
    },
    "analyst": {
        "kb_access": ["read"],
        "kg_access": ["read"],
        "agent_access": ["market_analysis", "location_recommender", "regulatory_advisor", "domain_specialist"],
        "domain_access": ["financial", "marketing", "cuisine"],
        "user_management": False,
        "data_sources_access": ["mongodb", "neo4j"],
        "memory_access": ["read"],
        "description": "Access to analytics and research capabilities"
    },
    "restaurant_owner": {
        "kb_access": ["read"],
        "kg_access": ["read"],
        "agent_access": ["location_recommender", "regulatory_advisor", "domain_specialist"],
        "domain_access": ["cuisine", "design", "staffing"],
        "user_management": False,
        "data_sources_access": ["mongodb"],
        "memory_access": ["read"],
        "description": "Access to location and regulatory information"
    },
    "operations": {
        "kb_access": ["read"],
        "kg_access": ["read"],
        "agent_access": ["domain_specialist"],
        "domain_access": ["staffing", "technology", "design"],
        "user_management": False,
        "data_sources_access": ["mongodb"],
        "memory_access": ["read"],
        "description": "Access to operational domain specialists"
    },
    "guest": {
        "kb_access": ["read"],
        "kg_access": ["read"],
        "agent_access": ["basic_query"],
        "domain_access": [],
        "user_management": False,
        "data_sources_access": ["limited"],
        "memory_access": [],
        "description": "Limited access to basic information only"
    }
}

# System settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
