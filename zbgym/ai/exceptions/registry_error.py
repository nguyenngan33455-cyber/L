"""
Registry Error Exception

Raised when agent registry operations fail.
"""

from zbgym.ai.exceptions.ai_error import AIError


class RegistryError(AIError):
    """
    Raised when agent registry operations fail.
    
    Examples:
        - Agent not found
        - Duplicate registration
        - Invalid agent type
    """
    
    def __init__(
        self,
        message: str,
        agent_type: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        """
        Initialize registry error.
        
        Args:
            message: Error message
            agent_type: Agent type being registered/looked up
            agent_id: Agent ID
        """
        super().__init__(message, agent_id)
        self.agent_type = agent_type
