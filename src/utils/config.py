"""
Configuration management for Code RAG System
Load from environment variables or defaults
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.3
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Vector DB Configuration
    CHROMADB_PATH: str = "data/processed/chromadb"
    CHROMADB_COLLECTION_NAME: str = "code_docs"
    
    # Chunking Configuration
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Retrieval Configuration
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.3
    
    # Repository Configuration
    REPO_CACHE_DIR: str = "data/raw/repos"
    MAX_REPO_SIZE_MB: int = 500
    
    # File Filtering
    SUPPORTED_EXTENSIONS: list = [".py", ".md", ".txt", ".java", ".js", ".cpp", ".c"]
    IGNORE_DIRS: list = [".git", "__pycache__", "node_modules", ".venv", "venv"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Performance
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Create necessary directories
Path(settings.CHROMADB_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.REPO_CACHE_DIR).mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(parents=True, exist_ok=True)