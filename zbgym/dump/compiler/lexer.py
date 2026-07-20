"""Lexer for C# decompilation tokenization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator


class TokenType(Enum):
    """Token types for C# decompilation."""

    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()

    # Keywords
    CLASS = auto()
    STRUCT = auto()
    ENUM = auto()
    INTERFACE = auto()
    NAMESPACE = auto()
    PUBLIC = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    INTERNAL = auto()
    STATIC = auto()
    SEALED = auto()
    ABSTRACT = auto()
    PARTIAL = auto()
    VOID = auto()
    VIRTUAL = auto()
    OVERRIDE = auto()
    READONLY = auto()
    CONST = auto()
    VOLATILE = auto()
    NEW = auto()
    THIS = auto()
    BASE = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    FOREACH = auto()
    WHILE = auto()
    DO = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    THROW = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    USING = auto()
    AS = auto()
    IS = auto()
    IN_KEYWORD = auto()  # renamed to avoid conflict
    REF = auto()
    OUT = auto()
    GET = auto()
    SET = auto()
    ADD = auto()
    REMOVE = auto()
    VALUE = auto()
    WHERE = auto()
    YIELD = auto()
    ASYNC = auto()
    AWAIT = auto()
    DYNAMIC = auto()
    NULL = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    AMPERSAND = auto()
    PIPE = auto()
    CARET = auto()
    BANG = auto()
    TILDE = auto()
    EQ = auto()
    LT = auto()
    GT = auto()
    QUESTION = auto()
    COLON = auto()
    DOT = auto()
    COMMA = auto()
    SEMICOLON = auto()

    # Compound operators
    EQ_EQ = auto()
    BANG_EQ = auto()
    LT_EQ = auto()
    GT_EQ = auto()
    AMPERSAND_AMPERSAND = auto()
    PIPE_PIPE = auto()
    PLUS_EQ = auto()
    MINUS_EQ = auto()
    STAR_EQ = auto()
    SLASH_EQ = auto()
    AMPERSAND_EQ = auto()
    PIPE_EQ = auto()
    CARET_EQ = auto()
    LT_LT = auto()
    GT_GT = auto()
    LT_LT_EQ = auto()
    GT_GT_EQ = auto()
    PLUS_PLUS = auto()
    MINUS_MINUS = auto()

    # Brackets
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    # Attributes
    LBRACKET_LBRACKET = auto()  # [[
    RBRACKET_RBRACKET = auto()  # ]]

    # Comments
    COMMENT = auto()
    DOCUMENTATION = auto()

    # Special
    ARROW = auto()  # =>
    DOUBLE_COLON = auto()  # ::
    NULL_COLON = auto()  # ?:
    HASH = auto()  # #

    # Whitespace
    NEWLINE = auto()
    INDENT = auto()

    # End of file
    EOF = auto()

    # Unknown
    UNKNOWN = auto()


@dataclass
class Token:
    """Represents a token in the C# code."""

    type: TokenType
    value: str
    line: int
    column: int
    offset: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class Lexer:
    """Lexical analyzer for C# decompilation."""

    KEYWORDS = {
        "class": TokenType.CLASS,
        "struct": TokenType.STRUCT,
        "enum": TokenType.ENUM,
        "interface": TokenType.INTERFACE,
        "namespace": TokenType.NAMESPACE,
        "public": TokenType.PUBLIC,
        "private": TokenType.PRIVATE,
        "protected": TokenType.PROTECTED,
        "internal": TokenType.INTERNAL,
        "static": TokenType.STATIC,
        "sealed": TokenType.SEALED,
        "abstract": TokenType.ABSTRACT,
        "partial": TokenType.PARTIAL,
        "void": TokenType.VOID,
        "virtual": TokenType.VIRTUAL,
        "override": TokenType.OVERRIDE,
        "readonly": TokenType.READONLY,
        "const": TokenType.CONST,
        "volatile": TokenType.VOLATILE,
        "new": TokenType.NEW,
        "this": TokenType.THIS,
        "base": TokenType.BASE,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "for": TokenType.FOR,
        "foreach": TokenType.FOREACH,
        "while": TokenType.WHILE,
        "do": TokenType.DO,
        "switch": TokenType.SWITCH,
        "case": TokenType.CASE,
        "default": TokenType.DEFAULT,
        "break": TokenType.BREAK,
        "continue": TokenType.CONTINUE,
        "return": TokenType.RETURN,
        "throw": TokenType.THROW,
        "try": TokenType.TRY,
        "catch": TokenType.CATCH,
        "finally": TokenType.FINALLY,
        "using": TokenType.USING,
        "as": TokenType.AS,
        "is": TokenType.IS,
        "in": TokenType.IN_KEYWORD,
        "ref": TokenType.REF,
        "out": TokenType.OUT,
        "get": TokenType.GET,
        "set": TokenType.SET,
        "add": TokenType.ADD,
        "remove": TokenType.REMOVE,
        "value": TokenType.VALUE,
        "where": TokenType.WHERE,
        "yield": TokenType.YIELD,
        "async": TokenType.ASYNC,
        "await": TokenType.AWAIT,
        "dynamic": TokenType.DYNAMIC,
        "null": TokenType.NULL,
        "true": TokenType.BOOLEAN,
        "false": TokenType.BOOLEAN,
    }

    SINGLE_CHAR_TOKENS = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.STAR,
        "/": TokenType.SLASH,
        "%": TokenType.PERCENT,
        "&": TokenType.AMPERSAND,
        "|": TokenType.PIPE,
        "^": TokenType.CARET,
        "!": TokenType.BANG,
        "~": TokenType.TILDE,
        "=": TokenType.EQ,
        "<": TokenType.LT,
        ">": TokenType.GT,
        "?": TokenType.QUESTION,
        ":": TokenType.COLON,
        ".": TokenType.DOT,
        ",": TokenType.COMMA,
        ";": TokenType.SEMICOLON,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "{": TokenType.LBRACE,
        "}": TokenType.RBRACE,
        "[": TokenType.LBRACKET,
        "]": TokenType.RBRACKET,
        "#": TokenType.HASH,
    }

    def __init__(self, source: str) -> None:
        """
        Initialize the lexer.

        Args:
            source: The source code to tokenize
        """
        self.source = source
        self.offset = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """
        Tokenize the entire source.

        Returns:
            List of tokens
        """
        while self.offset < len(self.source):
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column, self.offset))
        return self.tokens

    def _scan_token(self) -> None:
        """Scan the next token."""
        char = self.source[self.offset]

        # Skip whitespace (but not newlines for now)
        if char in " \t\r":
            self._advance()
            return

        # Newlines
        if char == "\n":
            self.tokens.append(Token(TokenType.NEWLINE, "\n", self.line, self.column, self.offset))
            self.line += 1
            self.column = 1
            self._advance()
            return

        # Comments
        if char == "/" and self._peek(1) == "/":
            self._scan_comment()
            return

        # Documentation comments
        if char == "/" and self._peek(1) == "/":
            self._scan_documentation()
            return

        # Attributes [[ ]]
        if char == "[" and self._peek(1) == "[":
            self.tokens.append(Token(TokenType.LBRACKET_LBRACKET, "[[", self.line, self.column, self.offset))
            self._advance()
            self._advance()
            return

        # Bracket ]]
        if char == "]" and self._peek(1) == "]":
            self.tokens.append(Token(TokenType.RBRACKET_RBRACKET, "]]", self.line, self.column, self.offset))
            self._advance()
            self._advance()
            return

        # String literal
        if char == '"':
            self._scan_string()
            return

        # Integer or float
        if char.isdigit() or (char == "." and self._peek(1).isdigit()):
            self._scan_number()
            return

        # Identifier or keyword
        if char.isalpha() or char == "_":
            self._scan_identifier()
            return

        # Compound operators
        if char == "=":
            if self._peek(1) == "=":
                self.tokens.append(Token(TokenType.EQ_EQ, "==", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == ">":
                self.tokens.append(Token(TokenType.ARROW, "=>", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.EQ, "=", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "!":
            if self._peek(1) == "=":
                self.tokens.append(Token(TokenType.BANG_EQ, "!=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.BANG, "!", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "<":
            if self._peek(1) == "=":
                self.tokens.append(Token(TokenType.LT_EQ, "<=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == "<":
                if self._peek(2) == "=":
                    self.tokens.append(Token(TokenType.LT_LT_EQ, "<<=", self.line, self.column, self.offset))
                    self._advance()
                    self._advance()
                    self._advance()
                else:
                    self.tokens.append(Token(TokenType.LT_LT, "<<", self.line, self.column, self.offset))
                    self._advance()
                    self._advance()
            else:
                self.tokens.append(Token(TokenType.LT, "<", self.line, self.column, self.offset))
                self._advance()
            return

        if char == ">":
            if self._peek(1) == "=":
                self.tokens.append(Token(TokenType.GT_EQ, ">=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == ">":
                if self._peek(2) == "=":
                    self.tokens.append(Token(TokenType.GT_GT_EQ, ">>=", self.line, self.column, self.offset))
                    self._advance()
                    self._advance()
                    self._advance()
                else:
                    self.tokens.append(Token(TokenType.GT_GT, ">>", self.line, self.column, self.offset))
                    self._advance()
                    self._advance()
            else:
                self.tokens.append(Token(TokenType.GT, ">", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "&":
            if self._peek(1) == "&":
                self.tokens.append(Token(TokenType.AMPERSAND_AMPERSAND, "&&", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == "=":
                self.tokens.append(Token(TokenType.AMPERSAND_EQ, "&=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.AMPERSAND, "&", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "|":
            if self._peek(1) == "|":
                self.tokens.append(Token(TokenType.PIPE_PIPE, "||", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == "=":
                self.tokens.append(Token(TokenType.PIPE_EQ, "|=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.PIPE, "|", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "+":
            if self._peek(1) == "+":
                self.tokens.append(Token(TokenType.PLUS_PLUS, "++", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == "=":
                self.tokens.append(Token(TokenType.PLUS_EQ, "+=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.PLUS, "+", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "-":
            if self._peek(1) == "-":
                self.tokens.append(Token(TokenType.MINUS_MINUS, "--", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == "=":
                self.tokens.append(Token(TokenType.MINUS_EQ, "-=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == ">":
                self.tokens.append(Token(TokenType.ARROW, "->", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.MINUS, "-", self.line, self.column, self.offset))
                self._advance()
            return

        if char == ":":
            if self._peek(1) == ":":
                self.tokens.append(Token(TokenType.DOUBLE_COLON, "::", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            elif self._peek(1) == "?":
                self.tokens.append(Token(TokenType.NULL_COLON, "?:", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.COLON, ":", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "?":
            if self._peek(1) == "?":
                self.tokens.append(Token(TokenType.NULL, "??", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.QUESTION, "?", self.line, self.column, self.offset))
                self._advance()
            return

        if char == "^":
            if self._peek(1) == "=":
                self.tokens.append(Token(TokenType.CARET_EQ, "^=", self.line, self.column, self.offset))
                self._advance()
                self._advance()
            else:
                self.tokens.append(Token(TokenType.CARET, "^", self.line, self.column, self.offset))
                self._advance()
            return

        # Single character tokens
        if char in self.SINGLE_CHAR_TOKENS:
            self.tokens.append(Token(self.SINGLE_CHAR_TOKENS[char], char, self.line, self.column, self.offset))
            self._advance()
            return

        # Unknown character
        self.tokens.append(Token(TokenType.UNKNOWN, char, self.line, self.column, self.offset))
        self._advance()

    def _scan_comment(self) -> None:
        """Scan a single-line comment."""
        start = self.offset
        self._advance()  # /
        self._advance()  # /

        while self.offset < len(self.source) and self.source[self.offset] != "\n":
            self._advance()

        value = self.source[start : self.offset]
        self.tokens.append(Token(TokenType.COMMENT, value, self.line, self.column, start))

    def _scan_documentation(self) -> None:
        """Scan a documentation comment."""
        start = self.offset
        self._advance()  # /
        self._advance()  # /

        while self.offset < len(self.source) and self.source[self.offset] != "\n":
            self._advance()

        value = self.source[start : self.offset]
        self.tokens.append(Token(TokenType.DOCUMENTATION, value, self.line, self.column, start))

    def _scan_string(self) -> None:
        """Scan a string literal."""
        start = self.offset
        self._advance()  # "

        while self.offset < len(self.source):
            char = self.source[self.offset]
            if char == '"':
                self._advance()
                break
            if char == "\\":
                self._advance()
                if self.offset < len(self.source):
                    self._advance()
            elif char == "\n":
                break
            else:
                self._advance()

        value = self.source[start : self.offset]
        self.tokens.append(Token(TokenType.STRING, value, self.line, self.column, start))

    def _scan_number(self) -> None:
        """Scan a number literal."""
        start = self.offset
        has_decimal = False

        while self.offset < len(self.source):
            char = self.source[self.offset]
            if char.isdigit():
                self._advance()
            elif char == "." and not has_decimal:
                has_decimal = True
                self._advance()
            elif char == "f" or char == "F" or char == "d" or char == "D" or char == "m" or char == "M" or char == "u" or char == "U" or char == "l" or char == "L":
                self._advance()
                break
            else:
                break

        value = self.source[start : self.offset]

        if has_decimal:
            self.tokens.append(Token(TokenType.FLOAT, value, self.line, self.column, start))
        else:
            self.tokens.append(Token(TokenType.INTEGER, value, self.line, self.column, start))

    def _scan_identifier(self) -> None:
        """Scan an identifier or keyword."""
        start = self.offset

        while self.offset < len(self.source):
            char = self.source[self.offset]
            if char.isalnum() or char == "_":
                self._advance()
            else:
                break

        value = self.source[start : self.offset]

        # Check if it's a keyword
        if value in self.KEYWORDS:
            self.tokens.append(Token(self.KEYWORDS[value], value, self.line, self.column, start))
        else:
            self.tokens.append(Token(TokenType.IDENTIFIER, value, self.line, self.column, start))

    def _peek(self, offset: int = 1) -> str:
        """Look ahead at a character."""
        pos = self.offset + offset
        if pos < len(self.source):
            return self.source[pos]
        return ""

    def _advance(self) -> None:
        """Advance the offset and update line/column."""
        self.offset += 1
        self.column += 1
