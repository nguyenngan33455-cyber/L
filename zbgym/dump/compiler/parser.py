"""AST parser for C# decompilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from zbgym.dump.compiler.lexer import Token, TokenType


@dataclass
class ASTNode:
    """Base class for all AST nodes."""

    line: int = 0
    column: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary."""
        result = {"type": self.__class__.__name__, "line": self.line, "column": self.column}
        for key, value in self.__dict__.items():
            if key not in ("line", "column") and not key.startswith("_"):
                if isinstance(value, ASTNode):
                    result[key] = value.to_dict()
                elif isinstance(value, list):
                    result[key] = [v.to_dict() if isinstance(v, ASTNode) else v for v in value]
                else:
                    result[key] = value
        return result


@dataclass
class NamespaceDecl(ASTNode):
    """Represents a namespace declaration."""

    name: str = ""
    members: list[ASTNode] = field(default_factory=list)


@dataclass
class ClassDecl(ASTNode):
    """Represents a class declaration."""

    modifiers: list[str] = field(default_factory=list)
    name: str = ""
    base_types: list[str] = field(default_factory=list)
    members: list[ASTNode] = field(default_factory=list)
    namespace: str = ""


@dataclass
class StructDecl(ASTNode):
    """Represents a struct declaration."""

    modifiers: list[str] = field(default_factory=list)
    name: str = ""
    members: list[ASTNode] = field(default_factory=list)
    namespace: str = ""


@dataclass
class EnumDecl(ASTNode):
    """Represents an enum declaration."""

    modifiers: list[str] = field(default_factory=list)
    name: str = ""
    base_type: str = "int"
    members: list[EnumMemberDecl] = field(default_factory=list)
    namespace: str = ""


@dataclass
class InterfaceDecl(ASTNode):
    """Represents an interface declaration."""

    modifiers: list[str] = field(default_factory=list)
    name: str = ""
    members: list[ASTNode] = field(default_factory=list)
    namespace: str = ""


@dataclass
class FieldDecl(ASTNode):
    """Represents a field declaration."""

    modifiers: list[str] = field(default_factory=list)
    type_name: str = ""
    name: str = ""
    default_value: Any = None


@dataclass
class PropertyDecl(ASTNode):
    """Represents a property declaration."""

    modifiers: list[str] = field(default_factory=list)
    type_name: str = ""
    name: str = ""
    getter: MethodDecl | None = None
    setter: MethodDecl | None = None
    getter_body: str = ""
    setter_body: str = ""


@dataclass
class MethodDecl(ASTNode):
    """Represents a method declaration."""

    modifiers: list[str] = field(default_factory=list)
    return_type: str = ""
    name: str = ""
    parameters: list[ParameterDecl] = field(default_factory=list)
    body: str = ""
    is_abstract: bool = False


@dataclass
class ParameterDecl(ASTNode):
    """Represents a parameter declaration."""

    type_name: str = ""
    name: str = ""
    default_value: Any = None


@dataclass
class EnumMemberDecl(ASTNode):
    """Represents an enum member declaration."""

    name: str = ""
    value: Any = None


@dataclass
class AttributeDecl(ASTNode):
    """Represents an attribute declaration."""

    name: str = ""
    arguments: list[Any] = field(default_factory=list)


class Parser:
    """Parser for C# decompilation AST generation."""

    def __init__(self, tokens: list[Token]) -> None:
        """
        Initialize the parser.

        Args:
            tokens: List of tokens from the lexer
        """
        self.tokens = tokens
        self.offset = 0

    def parse(self) -> list[ASTNode]:
        """
        Parse the tokens into an AST.

        Returns:
            List of top-level declarations
        """
        declarations: list[ASTNode] = []

        while not self._is_at_end():
            # Skip newlines
            while self._check(TokenType.NEWLINE):
                self._advance()

            if self._is_at_end():
                break

            # Parse namespace
            if self._check(TokenType.NAMESPACE):
                declarations.append(self._parse_namespace())
            # Parse class
            elif self._check(TokenType.CLASS):
                declarations.append(self._parse_class())
            # Parse struct
            elif self._check(TokenType.STRUCT):
                declarations.append(self._parse_struct())
            # Parse enum
            elif self._check(TokenType.ENUM):
                declarations.append(self._parse_enum())
            # Parse interface
            elif self._check(TokenType.INTERFACE):
                declarations.append(self._parse_interface())
            else:
                # Skip unknown tokens
                self._advance()

        return declarations

    def _parse_namespace(self) -> NamespaceDecl:
        """Parse a namespace declaration."""
        start = self._current()
        self._expect(TokenType.NAMESPACE)
        name = self._expect_identifier()
        self._expect(TokenType.LBRACE)

        members: list[ASTNode] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            while self._check(TokenType.NEWLINE):
                self._advance()

            if self._check(TokenType.RBRACE):
                break

            if self._check(TokenType.CLASS):
                members.append(self._parse_class())
            elif self._check(TokenType.STRUCT):
                members.append(self._parse_struct())
            elif self._check(TokenType.ENUM):
                members.append(self._parse_enum())
            elif self._check(TokenType.INTERFACE):
                members.append(self._parse_interface())
            else:
                self._advance()

        self._expect(TokenType.RBRACE)

        return NamespaceDecl(name=name, members=members, line=start.line, column=start.column)

    def _parse_class(self) -> ClassDecl:
        """Parse a class declaration."""
        start = self._current()
        modifiers = self._parse_modifiers()
        self._expect(TokenType.CLASS)

        name = self._expect_identifier()
        base_types: list[str] = []

        # Parse base types (after :)
        if self._check(TokenType.COLON):
            self._advance()
            while not self._check(TokenType.LBRACE) and not self._is_at_end():
                base_types.append(self._expect_identifier())
                if not self._check(TokenType.COMMA):
                    break
                self._advance()

        self._expect(TokenType.LBRACE)
        members = self._parse_class_members()
        self._expect(TokenType.RBRACE)

        return ClassDecl(
            modifiers=modifiers,
            name=name,
            base_types=base_types,
            members=members,
            line=start.line,
            column=start.column,
        )

    def _parse_struct(self) -> StructDecl:
        """Parse a struct declaration."""
        start = self._current()
        modifiers = self._parse_modifiers()
        self._expect(TokenType.STRUCT)

        name = self._expect_identifier()
        self._expect(TokenType.LBRACE)
        members = self._parse_class_members()
        self._expect(TokenType.RBRACE)

        return StructDecl(
            modifiers=modifiers,
            name=name,
            members=members,
            line=start.line,
            column=start.column,
        )

    def _parse_enum(self) -> EnumDecl:
        """Parse an enum declaration."""
        start = self._current()
        modifiers = self._parse_modifiers()
        self._expect(TokenType.ENUM)

        name = self._expect_identifier()
        base_type = "int"

        # Parse base type
        if self._check(TokenType.COLON):
            self._advance()
            base_type = self._expect_identifier()

        self._expect(TokenType.LBRACE)
        members = self._parse_enum_members()
        self._expect(TokenType.RBRACE)

        return EnumDecl(
            modifiers=modifiers,
            name=name,
            base_type=base_type,
            members=members,
            line=start.line,
            column=start.column,
        )

    def _parse_interface(self) -> InterfaceDecl:
        """Parse an interface declaration."""
        start = self._current()
        modifiers = self._parse_modifiers()
        self._expect(TokenType.INTERFACE)

        name = self._expect_identifier()
        self._expect(TokenType.LBRACE)
        members = self._parse_class_members()
        self._expect(TokenType.RBRACE)

        return InterfaceDecl(
            modifiers=modifiers,
            name=name,
            members=members,
            line=start.line,
            column=start.column,
        )

    def _parse_modifiers(self) -> list[str]:
        """Parse class/struct modifiers."""
        modifiers: list[str] = []
        while True:
            if self._check(TokenType.PUBLIC):
                modifiers.append("public")
                self._advance()
            elif self._check(TokenType.PRIVATE):
                modifiers.append("private")
                self._advance()
            elif self._check(TokenType.PROTECTED):
                modifiers.append("protected")
                self._advance()
            elif self._check(TokenType.INTERNAL):
                modifiers.append("internal")
                self._advance()
            elif self._check(TokenType.STATIC):
                modifiers.append("static")
                self._advance()
            elif self._check(TokenType.SEALED):
                modifiers.append("sealed")
                self._advance()
            elif self._check(TokenType.ABSTRACT):
                modifiers.append("abstract")
                self._advance()
            elif self._check(TokenType.PARTIAL):
                modifiers.append("partial")
                self._advance()
            elif self._check(TokenType.READONLY):
                modifiers.append("readonly")
                self._advance()
            elif self._check(TokenType.VIRTUAL):
                modifiers.append("virtual")
                self._advance()
            elif self._check(TokenType.OVERRIDE):
                modifiers.append("override")
                self._advance()
            elif self._check(TokenType.CONST):
                modifiers.append("const")
                self._advance()
            else:
                break
        return modifiers

    def _parse_class_members(self) -> list[ASTNode]:
        """Parse class/struct members."""
        members: list[ASTNode] = []

        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            # Skip newlines
            while self._check(TokenType.NEWLINE):
                self._advance()

            if self._check(TokenType.RBRACE):
                break

            # Check for nested types
            if self._check(TokenType.CLASS):
                members.append(self._parse_class())
                continue
            if self._check(TokenType.STRUCT):
                members.append(self._parse_struct())
                continue
            if self._check(TokenType.ENUM):
                members.append(self._parse_enum())
                continue

            # Check for property (has getter/setter)
            if self._is_property_start():
                members.append(self._parse_property())
                continue

            # Otherwise, it's a field or method
            modifiers = self._parse_modifiers()

            # Check for return type
            if self._check(TokenType.IDENTIFIER) or self._is_type_keyword():
                type_name = self._expect_type()
                name_token = self._current()

                if self._check(TokenType.LPAREN):
                    # It's a method
                    method = self._parse_method_with_modifiers(
                        modifiers, type_name, name_token.value
                    )
                    members.append(method)
                else:
                    # It's a field
                    field = self._parse_field_with_type(modifiers, type_name, name_token.value)
                    members.append(field)
            else:
                # Skip unknown
                self._advance()

        return members

    def _is_property_start(self) -> bool:
        """Check if current position starts a property."""
        # Look ahead for get/set without modifiers
        offset = self.offset
        while self._check(TokenType.NEWLINE):
            self._advance()

        is_start = self._check(TokenType.IDENTIFIER) or (
            self._is_type_keyword()
            and self._peek_is_identifier_or_type()
            and self._has_get_or_set_ahead()
        )

        self.offset = offset
        return is_start

    def _has_get_or_set_ahead(self) -> bool:
        """Check if there's a get or set keyword ahead."""
        depth = 0
        while not self._is_at_end():
            if self._check(TokenType.LBRACE):
                depth += 1
            elif self._check(TokenType.RBRACE):
                if depth == 0:
                    break
                depth -= 1
            elif depth == 0 and (self._check(TokenType.GET) or self._check(TokenType.SET)):
                return True
            self._advance()
        return False

    def _peek_is_identifier_or_type(self) -> bool:
        """Check if peeked token is identifier or type."""
        offset = self.offset
        while self._check(TokenType.NEWLINE):
            self._advance()
        result = self._check(TokenType.IDENTIFIER) or self._is_type_keyword()
        self.offset = offset
        return result

    def _parse_property(self) -> PropertyDecl:
        """Parse a property declaration."""
        start = self._current()
        modifiers = self._parse_modifiers()
        type_name = self._expect_type()
        name = self._expect_identifier()

        self._expect(TokenType.LBRACE)

        getter: MethodDecl | None = None
        setter: MethodDecl | None = None
        getter_body = ""
        setter_body = ""

        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            if self._check(TokenType.GET):
                self._advance()
                getter_body = self._parse_method_body()
                getter = MethodDecl(name="get_" + name)
            elif self._check(TokenType.SET):
                self._advance()
                setter_body = self._parse_method_body()
                setter = MethodDecl(name="set_" + name)
            else:
                self._advance()

        self._expect(TokenType.RBRACE)

        return PropertyDecl(
            modifiers=modifiers,
            type_name=type_name,
            name=name,
            getter=getter,
            setter=setter,
            getter_body=getter_body,
            setter_body=setter_body,
            line=start.line,
            column=start.column,
        )

    def _parse_field(self) -> FieldDecl:
        """Parse a field declaration."""
        start = self._current()
        modifiers = self._parse_modifiers()
        type_name = self._expect_type()
        name = self._expect_identifier()
        default_value = None

        if self._check(TokenType.EQ):
            self._advance()
            default_value = self._parse_expression()

        self._expect_semicolon()

        return FieldDecl(
            modifiers=modifiers,
            type_name=type_name,
            name=name,
            default_value=default_value,
            line=start.line,
            column=start.column,
        )

    def _parse_field_with_type(self, modifiers: list[str], type_name: str, name: str) -> FieldDecl:
        """Parse a field with pre-determined type."""
        start = self._current()
        default_value = None

        if self._check(TokenType.EQ):
            self._advance()
            default_value = self._parse_expression()

        self._expect_semicolon()

        return FieldDecl(
            modifiers=modifiers,
            type_name=type_name,
            name=name,
            default_value=default_value,
            line=start.line,
            column=start.column,
        )

    def _parse_method(self) -> MethodDecl:
        """Parse a method declaration."""
        start = self._current()
        modifiers = self._parse_modifiers()
        return_type = self._expect_type()
        name = self._expect_identifier()
        return self._parse_method_with_modifiers(modifiers, return_type, name)

    def _parse_method_with_modifiers(
        self, modifiers: list[str], return_type: str, name: str
    ) -> MethodDecl:
        """Parse a method with pre-determined modifiers and return type."""
        start = self._current()
        parameters = self._parse_parameters()
        body = ""
        is_abstract = False

        if self._check(TokenType.SEMICOLON):
            self._advance()
            is_abstract = True
        else:
            body = self._parse_method_body()

        return MethodDecl(
            modifiers=modifiers,
            return_type=return_type,
            name=name,
            parameters=parameters,
            body=body,
            is_abstract=is_abstract,
            line=start.line,
            column=start.column,
        )

    def _parse_parameters(self) -> list[ParameterDecl]:
        """Parse method parameters."""
        self._expect(TokenType.LPAREN)
        parameters: list[ParameterDecl] = []

        if not self._check(TokenType.RPAREN):
            while True:
                param_type = self._expect_type()
                param_name = self._expect_identifier()
                parameters.append(ParameterDecl(type_name=param_type, name=param_name))

                if not self._check(TokenType.COMMA):
                    break
                self._advance()

        self._expect(TokenType.RPAREN)
        return parameters

    def _parse_method_body(self) -> str:
        """Parse method body as raw text."""
        self._expect(TokenType.LBRACE)
        depth = 1
        body_start = self.offset

        while depth > 0 and not self._is_at_end():
            if self._check(TokenType.LBRACE):
                depth += 1
            elif self._check(TokenType.RBRACE):
                depth -= 1
            self._advance()

        return self.source_text(
            self.tokens[0].offset, self.tokens[self.offset - 1].offset if self.offset > 0 else 0
        )

    def _parse_enum_members(self) -> list[EnumMemberDecl]:
        """Parse enum members."""
        members: list[EnumMemberDecl] = []

        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            while self._check(TokenType.NEWLINE):
                self._advance()

            if self._check(TokenType.RBRACE):
                break

            name = self._expect_identifier()
            value = None

            if self._check(TokenType.EQ):
                self._advance()
                value = self._parse_expression()

            members.append(EnumMemberDecl(name=name, value=value))

            if not self._check(TokenType.RBRACE):
                self._expect_semicolon_or_newline()

        return members

    def _parse_expression(self) -> Any:
        """Parse a simple expression."""
        token = self._current()

        if self._check(TokenType.INTEGER):
            self._advance()
            return int(token.value)
        if self._check(TokenType.FLOAT):
            self._advance()
            return float(token.value)
        if self._check(TokenType.STRING):
            self._advance()
            return token.value
        if self._check(TokenType.BOOLEAN):
            self._advance()
            return token.value == "true"
        if self._check(TokenType.NULL):
            self._advance()
            return None
        if self._check(TokenType.IDENTIFIER):
            self._advance()
            return token.value
        self._advance()
        return token.value

    def _is_type_keyword(self) -> bool:
        """Check if current token is a type keyword."""
        return self._check(TokenType.VOID)

    @property
    def source_text(self) -> str:
        """Get the source text."""
        return self.tokens[0].value if self.tokens else ""

    def _current(self) -> Token:
        """Get current token."""
        if self.offset < len(self.tokens):
            return self.tokens[self.offset]
        return self.tokens[-1]

    def _peek(self) -> Token:
        """Peek at next token."""
        if self.offset + 1 < len(self.tokens):
            return self.tokens[self.offset + 1]
        return self.tokens[-1]

    def _advance(self) -> Token:
        """Advance and return current token."""
        if self.offset < len(self.tokens):
            self.offset += 1
        return self.tokens[self.offset - 1]

    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type."""
        return self._current().type == token_type

    def _is_at_end(self) -> bool:
        """Check if at end of tokens."""
        return self._current().type == TokenType.EOF

    def _expect(self, token_type: TokenType) -> Token:
        """Expect and consume a token of given type."""
        token = self._current()
        if token.type != token_type:
            self._advance()  # Still advance to avoid infinite loops
            return token
        self._advance()
        return token

    def _expect_identifier(self) -> str:
        """Expect and consume an identifier."""
        token = self._current()
        if token.type != TokenType.IDENTIFIER:
            self._advance()
            return ""
        self._advance()
        return token.value

    def _expect_type(self) -> str:
        """Expect and consume a type."""
        type_name = ""

        # Handle simple types
        if self._check(TokenType.VOID):
            type_name = self._current().value
            self._advance()
        elif self._check(TokenType.IDENTIFIER):
            type_name = self._current().value
            self._advance()

            # Handle generics (e.g., List<T>)
            if self._check(TokenType.LT):
                generic_start = self.offset - 1
                self._advance()
                depth = 1
                while depth > 0 and not self._is_at_end():
                    if self._check(TokenType.LT):
                        depth += 1
                    elif self._check(TokenType.GT):
                        depth -= 1
                    self._advance()
                # Reconstruct generic type
                type_name = "".join(t.value for t in self.tokens[generic_start : self.offset])

        return type_name

    def _expect_semicolon(self) -> None:
        """Expect and consume a semicolon."""
        self._expect(TokenType.SEMICOLON)

    def _expect_semicolon_or_newline(self) -> None:
        """Expect semicolon or newline."""
        if self._check(TokenType.SEMICOLON):
            self._advance()
        else:
            while self._check(TokenType.NEWLINE):
                self._advance()
