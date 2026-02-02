"""
Base agent class that all agents inherit from.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, openai_client):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent
            openai_client: OpenAI client instance
        """
        self.name = name
        self.openai_client = openai_client
        self.logger = logger.bind(agent=name)
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the agent's task.
        
        Args:
            task: Task description and parameters
            context: Additional context from previous agents
            
        Returns:
            Result dictionary with status and data
        """
        pass
    
    def log(self, message: str, level: str = "info"):
        """Log a message with the agent's context."""
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message)

