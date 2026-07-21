"""
Exceptions for ZBGym Interfaces.

This module defines custom exceptions used by the interface layer.
These exceptions provide clear error messages when interface
contracts are violated.
"""


class InterfaceError(Exception):
    """
    Base exception for interface-related errors.
    
    Raised when there are issues with interface implementation
    or contract violations.
    """
    pass


class StateError(InterfaceError):
    """
    Exception raised for game state errors.
    
    Raised when:
    - State conversion fails
    - Invalid state access
    - State serialization/deserialization errors
    """
    pass


class EntityError(InterfaceError):
    """
    Exception raised for entity errors.
    
    Raised when:
    - Entity not found
    - Invalid entity access
    - Entity type mismatch
    """
    pass


class ActionError(InterfaceError):
    """
    Exception raised for action errors.
    
    Raised when:
    - Invalid action
    - Action not allowed
    - Action type mismatch
    """
    pass


class ProviderError(InterfaceError):
    """
    Exception raised for provider errors.
    
    Raised when:
    - Provider initialization fails
    - Provider computation fails
    - Provider not available
    """
    pass
