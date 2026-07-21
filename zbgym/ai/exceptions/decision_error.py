"""
Decision Error Exception

Raised when decision-making fails.
"""

from zbgym.ai.exceptions.ai_error import AIError


class DecisionError(AIError):
    """
    Raised when decision-making fails.
    
    Examples:
        - Invalid context
        - No valid actions available
        - Decision timeout
    """
    
    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        context_info: dict | None = None,
    ) -> None:
        """
        Initialize decision error.
        
        Args:
            message: Error message
            agent_id: Agent ID
            context_info: Additional context information
        """
        super().__init__(message, agent_id)
        self.context_info = context_info or {}
