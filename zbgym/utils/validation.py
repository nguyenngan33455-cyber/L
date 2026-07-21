"""
State Validation Module for ZBGym

Provides validation functions to ensure game state integrity.
All important objects must validate themselves on creation and modification.
"""

from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    """Raised when state validation fails."""
    pass


def validate_positive(value: float, name: str, min_value: float = 0.0) -> None:
    """
    Validate that a numeric value is positive.
    
    Args:
        value: Value to validate
        name: Name for error message
        min_value: Minimum allowed value (exclusive)
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric, got {type(value).__name__}")
    if value < min_value:
        raise ValidationError(f"{name} must be >= {min_value}, got {value}")


def validate_positive_or_zero(value: float, name: str) -> None:
    """Validate that a value is non-negative."""
    validate_positive(value, name, min_value=0.0)


def validate_in_range(
    value: float,
    name: str,
    min_value: float,
    max_value: float
) -> None:
    """
    Validate that a value is within a range.
    
    Args:
        value: Value to validate
        name: Name for error message
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric, got {type(value).__name__}")
    if value < min_value or value > max_value:
        raise ValidationError(
            f"{name} must be in range [{min_value}, {max_value}], got {value}"
        )


def validate_not_none(value: Any, name: str) -> None:
    """Validate that a value is not None."""
    if value is None:
        raise ValidationError(f"{name} cannot be None")


def validate_not_empty(value: str | list | tuple | dict, name: str) -> None:
    """Validate that a collection is not empty."""
    if not value:
        raise ValidationError(f"{name} cannot be empty")


def validate_id(value: str, name: str) -> None:
    """Validate that a string is a valid identifier."""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValidationError(f"{name} cannot be empty or whitespace")


def validate_enum_value(value: Any, name: str, valid_values: set | list) -> None:
    """Validate that a value is one of the allowed values."""
    if value not in valid_values:
        raise ValidationError(
            f"{name} must be one of {valid_values}, got {value}"
        )


def validate_health(health: float, max_health: float, name: str = "health") -> None:
    """Validate health values."""
    validate_positive_or_zero(health, f"{name}")
    validate_positive(max_health, f"{name}_max")
    if health > max_health:
        raise ValidationError(
            f"{name} ({health}) cannot exceed {name}_max ({max_health})"
        )


def validate_position(x: float, y: float, width: float, height: float) -> None:
    """Validate position is within bounds."""
    if x < 0 or x > width:
        raise ValidationError(f"x ({x}) must be in range [0, {width}]")
    if y < 0 or y > height:
        raise ValidationError(f"y ({y}) must be in range [0, {height}]")


def validate_radius(radius: float, name: str = "radius") -> None:
    """Validate radius is positive."""
    validate_positive(radius, name)


def clamp_health(health: float, max_health: float) -> float:
    """Clamp health to valid range."""
    return max(0.0, min(health, max_health))


def clamp_position(x: float, y: float, width: float, height: float, margin: float = 0.0) -> tuple[float, float]:
    """Clamp position to valid bounds."""
    return (
        max(margin, min(x, width - margin)),
        max(margin, min(y, height - margin))
    )
