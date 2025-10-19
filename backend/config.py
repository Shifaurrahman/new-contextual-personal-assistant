import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./contextual_assistant.db")
    
    # Agent Configuration
    MAX_ITERATIONS = 5
    AGENT_VERBOSE = True
    
    # Card Configuration
    CARD_TYPES = ["task", "reminder", "idea", "note"]
    PRIORITY_LEVELS = ["low", "medium", "high", "urgent"]
    
    # Context Configuration
    MAX_CONTEXT_ITEMS = 50
    SIMILARITY_THRESHOLD = 0.7
    
    # Thinking Agent Configuration
    THINKING_AGENT_SCHEDULE = 3600  # Run every hour (in seconds)
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        return True