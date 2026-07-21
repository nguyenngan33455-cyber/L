"""Tests for dump validation tools."""

import tempfile

from zbgym.tools.validate_dump import (
    validate_all,
    validate_class_structure,
    validate_enum_consistency,
)


class TestValidateDump:
    """Tests for dump validation functions."""

    def test_validate_enum_consistency_valid(self):
        """Test validation with valid enum."""
        content = """
public enum CharacterEnum
{
    public const CharacterEnum None = 0;
    public const CharacterEnum Fox = 1;
    public const CharacterEnum Turtle = 2;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cs", delete=False) as f:
            f.write(content)
            f.flush()

            result = validate_enum_consistency(f.name)

            assert result.is_valid == True
            assert len(result.errors) == 0

    def test_validate_enum_consistency_with_gaps(self):
        """Test validation detects gaps in enum."""
        content = """
public enum CharacterEnum
{
    public const CharacterEnum None = 0;
    public const CharacterEnum Fox = 1;
    public const CharacterEnum Turtle = 3;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cs", delete=False) as f:
            f.write(content)
            f.flush()

            result = validate_enum_consistency(f.name)

            # Gaps should be warnings, not errors
            assert 2 in result.warnings or len(result.warnings) > 0

    def test_validate_class_structure_balanced_braces(self):
        """Test validation with balanced braces."""
        content = """
public class TestClass
{
    public int value;
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cs", delete=False) as f:
            f.write(content)
            f.flush()

            result = validate_class_structure(f.name)

            assert result.is_valid == True

    def test_validate_class_structure_unbalanced_braces(self):
        """Test validation detects unbalanced braces."""
        content = """
public class TestClass
{
    public int value;
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cs", delete=False) as f:
            f.write(content)
            f.flush()

            result = validate_class_structure(f.name)

            assert result.is_valid == False
            assert len(result.errors) > 0

    def test_validate_class_structure_duplicate_classes(self):
        """Test validation detects duplicate class definitions."""
        content = """
public class TestClass { }
public class TestClass { }
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cs", delete=False) as f:
            f.write(content)
            f.flush()

            result = validate_class_structure(f.name)

            assert result.is_valid == False

    def test_validate_all(self):
        """Test combined validation."""
        content = """
public enum TestEnum
{
    public const TestEnum A = 0;
    public const TestEnum B = 1;
}
public class TestClass { }
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cs", delete=False) as f:
            f.write(content)
            f.flush()

            result = validate_all(f.name)

            assert result.is_valid == True


class TestValidationResult:
    """Tests for ValidationResult namedtuple."""

    def test_result_attributes(self):
        """Test result has expected attributes."""
        from zbgym.tools.validate_dump import ValidationResult

        result = ValidationResult(is_valid=True, errors=[], warnings=["test warning"])

        assert result.is_valid == True
        assert result.errors == []
        assert result.warnings == ["test warning"]
