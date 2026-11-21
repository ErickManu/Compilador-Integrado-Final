"""Análisis léxico del subconjunto académico de Java."""

import json
from dataclasses import dataclass


class LexerError(ValueError):
    """Error de reconocimiento de un carácter o literal."""

    def __init__(self, message, tokens=()):
        super().__init__(message)
        self.tokens = list(tokens)


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    line: int
    column: int


KEYWORDS = {
    "int": "INT", "double": "DOUBLE", "String": "STRING_TYPE",
    "boolean": "BOOLEAN_TYPE", "true": "TRUE", "false": "FALSE",
    "if": "IF", "else": "ELSE", "while": "WHILE",
    "System": "SYSTEM", "out": "OUT", "println": "PRINTLN",
}
SYMBOLS = {
    "+": "PLUS", "-": "MINUS", "*": "MULTIPLY", "/": "DIVIDE",
    "%": "MODULO", "=": "ASSIGN", "==": "EQUAL", "!=": "NOT_EQUAL",
    ">": "GREATER", "<": "LESS", ">=": "GREATER_EQUAL",
    "<=": "LESS_EQUAL", "&&": "AND", "||": "OR", "!": "NOT",
    "(": "LPAREN", ")": "RPAREN", "{": "LBRACE", "}": "RBRACE",
    ";": "SEMICOLON", ".": "DOT",
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> str:
        position = self.position + offset
        return self.source[position] if position < len(self.source) else ""

    def _advance(self) -> str:
        char = self.source[self.position]
        self.position += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _error(self, message: str, line: int, column: int):
        raise LexerError(f"Error léxico en línea {line}, columna {column}:\n{message}", self.tokens)

    def tokenize(self) -> list[Token]:
        tokens = []
        self.tokens = tokens
        while self.position < len(self.source):
            char = self._peek()
            if char.isspace():
                self._advance()
                continue
            if char == "/" and self._peek(1) == "/":
                while self._peek() and self._peek() not in "\r\n":
                    self._advance()
                continue

            start, line, column = self.position, self.line, self.column
            if char.isascii() and (char.isalpha() or char == "_"):
                while self._peek() and self._peek().isascii() and (
                    self._peek().isalnum() or self._peek() == "_"
                ):
                    self._advance()
                value = self.source[start:self.position]
                tokens.append(Token(KEYWORDS.get(value, "IDENTIFIER"), value, line, column))
                continue

            if char in "0123456789":
                while self._peek() and self._peek() in "0123456789":
                    self._advance()
                if self._peek() == "." and self._peek(1) and self._peek(1) in "0123456789":
                    self._advance()
                    while self._peek() and self._peek() in "0123456789":
                        self._advance()
                tokens.append(Token("NUMBER", self.source[start:self.position], line, column))
                continue

            if char == '"':
                self._advance()
                while self._peek() and self._peek() != '"':
                    if ord(self._peek()) < 32:
                        self._error("La cadena contiene un salto de línea o carácter de control.", line, column)
                    if self._peek() == "\\":
                        self._advance()
                        if not self._peek():
                            self._error("Cadena sin comillas de cierre.", line, column)
                        if self._peek() not in '"\\nrtbf':
                            self._error("Secuencia de escape no soportada.", self.line, self.column)
                    self._advance()
                if not self._peek():
                    self._error("Cadena sin comillas de cierre.", line, column)
                self._advance()
                value = self.source[start:self.position]
                # La validación y los escapes coinciden con los de JSON.
                json.loads(value)
                tokens.append(Token("STRING_LITERAL", value, line, column))
                continue

            pair = self.source[self.position:self.position + 2]
            symbol = pair if pair in SYMBOLS else char
            if symbol not in SYMBOLS:
                self._error(f"Carácter no reconocido: {char!r}.", line, column)
            for _ in symbol:
                self._advance()
            tokens.append(Token(SYMBOLS[symbol], symbol, line, column))

        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()
