"""
Configuration management for the Web Scraping Agent system.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-3.5-turbo"  # Using GPT-3.5-turbo (more accessible, can change to gpt-4 if available)
    
    # Browser Configuration
    BROWSER_HEADLESS = False  # Show browser so user can see what's happening
    BROWSER_TIMEOUT = 30000  # 30 seconds
    PAGE_LOAD_TIMEOUT = 60000  # 60 seconds
    
    # Agent Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # Logging
    LOG_LEVEL = "INFO"
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")

