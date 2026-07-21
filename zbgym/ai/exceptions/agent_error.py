"""
Agent Error Exception

Raised when agent operations fail.
"""

from zbgym.ai.exceptions.ai_error import AIError


class AgentError(AIError):
    """
    Raised when agent operations fail.
    
    Examples:
        - Initialization failure
        - Reset failure
        - Invalid state transition
    """
    
    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        operation: str | None = None,
    ) -> None:
        """
        Initialize agent error.
        
        Args:
            message: Error message
            agent_id: Agent ID
            operation: Operation that failed
        """
        super().__init__(message, agent_id)
        self.operation = operation
    
    def __str__(self) -> str:
        base = super().__str__()
        if self.operation:
            return f"{base} (operation: {self.operation})"
        return base
