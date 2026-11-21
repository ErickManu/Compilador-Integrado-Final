"""Parser de descenso recursivo y nodos de la representación interna (AST)."""

import json
from dataclasses import dataclass

from lexer import Token


class ParserError(ValueError):
    """La secuencia de tokens no cumple la gramática."""


@dataclass
class Literal:
    value: str
    kind: str


@dataclass
class Identifier:
    name: str


@dataclass
class BinaryExpression:
    left: "Expression"
    operator: str
    right: "Expression"


@dataclass
class UnaryExpression:
    operator: str
    operand: "Expression"


Expression = Literal | Identifier | BinaryExpression | UnaryExpression


@dataclass
class VariableDeclaration:
    variable_type: str
    name: str
    initializer: Expression | None


@dataclass
class Assignment:
    name: str
    value: Expression


@dataclass
class PrintStatement:
    expression: Expression


@dataclass
class IfStatement:
    condition: Expression
    then_body: list["Statement"]
    else_body: list["Statement"] | None


@dataclass
class WhileStatement:
    condition: Expression
    body: list["Statement"]


Statement = VariableDeclaration | Assignment | PrintStatement | IfStatement | WhileStatement


@dataclass
class Program:
    statements: list[Statement]


TYPE_TOKENS = {"INT", "DOUBLE", "STRING_TYPE", "BOOLEAN_TYPE"}


class Parser:
    def __init__(self, tokens: list[Token]):
        if not tokens or tokens[-1].type != "EOF":
            raise ValueError("La lista de tokens debe terminar con EOF.")
        self.tokens = tokens
        self.position = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def _advance(self) -> Token:
        token = self.current
        if token.type != "EOF":
            self.position += 1
        return token

    def _match(self, token_type: str) -> bool:
        if self.current.type == token_type:
            self._advance()
            return True
        return False

    def _error(self, message: str):
        token = self.current
        raise ParserError(
            f"Error sintáctico en línea {token.line}, columna {token.column}:\n{message}"
        )

    def _expect(self, token_type: str, label: str) -> Token:
        if self.current.type != token_type:
            self._error(f"Se esperaba {label}.")
        return self._advance()

    def parse(self) -> Program:
        statements = []
        while self.current.type != "EOF":
            statements.append(self._statement())
        return Program(statements)

    def _statement(self) -> Statement:
        token_type = self.current.type
        if token_type in TYPE_TOKENS:
            variable_type = self._advance().value
            name = self._expect("IDENTIFIER", "un identificador").value
            initializer = self._expression() if self._match("ASSIGN") else None
            self._expect("SEMICOLON", "';'")
            return VariableDeclaration(variable_type, name, initializer)
        if token_type == "IDENTIFIER":
            name = self._advance().value
            self._expect("ASSIGN", "'='")
            value = self._expression()
            self._expect("SEMICOLON", "';'")
            return Assignment(name, value)
        if token_type == "SYSTEM":
            self._advance()
            for expected, label in (
                ("DOT", "'.'"), ("OUT", "'out'"), ("DOT", "'.'"),
                ("PRINTLN", "'println'"), ("LPAREN", "'('"),
            ):
                self._expect(expected, label)
            expression = self._expression()
            self._expect("RPAREN", "')'")
            self._expect("SEMICOLON", "';'")
            return PrintStatement(expression)
        if token_type == "IF":
            self._advance()
            condition = self._condition()
            then_body = self._block()
            else_body = self._block() if self._match("ELSE") else None
            return IfStatement(condition, then_body, else_body)
        if token_type == "WHILE":
            self._advance()
            condition = self._condition()
            return WhileStatement(condition, self._block())
        self._error("Se esperaba una declaración, asignación, impresión, 'if' o 'while'.")

    def _condition(self) -> Expression:
        self._expect("LPAREN", "'('")
        condition = self._expression()
        self._expect("RPAREN", "')'")
        return condition

    def _block(self) -> list[Statement]:
        self._expect("LBRACE", "'{'")
        statements = []
        while self.current.type not in {"RBRACE", "EOF"}:
            statements.append(self._statement())
        self._expect("RBRACE", "'}'")
        return statements

    # Cada nivel consume operadores de menor a mayor precedencia.
    PRECEDENCE = (
        {"OR"}, {"AND"}, {"EQUAL", "NOT_EQUAL"},
        {"GREATER", "LESS", "GREATER_EQUAL", "LESS_EQUAL"},
        {"PLUS", "MINUS"}, {"MULTIPLY", "DIVIDE", "MODULO"},
    )

    def _expression(self, level: int = 0) -> Expression:
        if level == len(self.PRECEDENCE):
            return self._unary()
        expression = self._expression(level + 1)
        while self.current.type in self.PRECEDENCE[level]:
            operator = self._advance().value
            expression = BinaryExpression(expression, operator, self._expression(level + 1))
        return expression

    def _unary(self) -> Expression:
        if self.current.type in {"NOT", "MINUS", "PLUS"}:
            return UnaryExpression(self._advance().value, self._unary())
        return self._primary()

    def _primary(self) -> Expression:
        token = self.current
        if self._match("NUMBER"):
            # Evita que ceros iniciales se interpreten como octales en el destino.
            integer, dot, fraction = token.value.partition(".")
            normalized = (integer.lstrip("0") or "0") + dot + fraction
            return Literal(normalized, "number")
        if self._match("STRING_LITERAL"):
            return Literal(json.loads(token.value), "string")
        if self.current.type in {"TRUE", "FALSE"}:
            return Literal(self._advance().value, "boolean")
        if self._match("IDENTIFIER"):
            return Identifier(token.value)
        if self._match("LPAREN"):
            expression = self._expression()
            self._expect("RPAREN", "')'")
            return expression
        self._error("Se esperaba un valor, identificador o expresión entre paréntesis.")


def parse(tokens: list[Token]) -> Program:
    return Parser(tokens).parse()
