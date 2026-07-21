"""
AI Error Base Exception

Base exception for all AI-related errors.
"""


class AIError(Exception):
    """
    Base exception for AI system errors.
    
    All AI-related exceptions should inherit from this class.
    
    Attributes:
        message: Error message
        agent_id: Associated agent ID if applicable
    """
    
    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
    ) -> None:
        """
        Initialize AI error.
        
        Args:
            message: Error message
            agent_id: Associated agent ID
        """
        super().__init__(message)
        self.message = message
        self.agent_id = agent_id
    
    def __str__(self) -> str:
        if self.agent_id:
            return f"[Agent {self.agent_id}] {self.message}"
        return self.message
