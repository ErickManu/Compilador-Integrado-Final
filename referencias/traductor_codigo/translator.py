"""Generación de código a partir del AST, sin reemplazos sobre el fuente."""

import json

from lexer import tokenize
from parser import (
    Assignment, BinaryExpression, Identifier, IfStatement, Literal, PrintStatement,
    Program, UnaryExpression, VariableDeclaration, WhileStatement, parse,
)


class Translator:
    CPP_TYPES = {"int": "int", "double": "double", "String": "string", "boolean": "bool"}

    def __init__(self, target: str):
        if target not in {"JavaScript", "C++"}:
            raise ValueError("El lenguaje destino debe ser JavaScript o C++.")
        self.target = target
        self.uses_strings = False

    def _expression(self, expression) -> str:
        if isinstance(expression, Literal):
            if expression.kind == "string":
                self.uses_strings = True
                return json.dumps(expression.value, ensure_ascii=False)
            return expression.value
        if isinstance(expression, Identifier):
            return expression.name
        if isinstance(expression, UnaryExpression):
            return f"({expression.operator}{self._expression(expression.operand)})"
        if isinstance(expression, BinaryExpression):
            left = self._expression(expression.left)
            right = self._expression(expression.right)
            return f"({left} {expression.operator} {right})"
        raise TypeError(f"Expresión desconocida: {type(expression).__name__}")

    def _statements(self, statements: list, level: int) -> list[str]:
        lines = []
        indent = "    " * level
        for statement in statements:
            if isinstance(statement, VariableDeclaration):
                if statement.variable_type == "String":
                    self.uses_strings = True
                variable_type = "let" if self.target == "JavaScript" else self.CPP_TYPES[statement.variable_type]
                initializer = ""
                if statement.initializer is not None:
                    initializer = " = " + self._expression(statement.initializer)
                lines.append(f"{indent}{variable_type} {statement.name}{initializer};")
            elif isinstance(statement, Assignment):
                lines.append(f"{indent}{statement.name} = {self._expression(statement.value)};")
            elif isinstance(statement, PrintStatement):
                value = self._expression(statement.expression)
                text = f"console.log({value});" if self.target == "JavaScript" else f"cout << {value} << endl;"
                lines.append(indent + text)
            elif isinstance(statement, IfStatement):
                lines.append(f"{indent}if ({self._expression(statement.condition)}) {{")
                lines.extend(self._statements(statement.then_body, level + 1))
                if statement.else_body is not None:
                    lines.append(indent + "} else {")
                    lines.extend(self._statements(statement.else_body, level + 1))
                lines.append(indent + "}")
            elif isinstance(statement, WhileStatement):
                lines.append(f"{indent}while ({self._expression(statement.condition)}) {{")
                lines.extend(self._statements(statement.body, level + 1))
                lines.append(indent + "}")
            else:
                raise TypeError(f"Instrucción desconocida: {type(statement).__name__}")
        return lines

    def translate(self, program: Program) -> str:
        self.uses_strings = False
        if self.target == "JavaScript":
            lines = self._statements(program.statements, 0)
        else:
            body = self._statements(program.statements, 1)
            lines = ["#include <iostream>"]
            if self.uses_strings:
                lines.append("#include <string>")
            lines.extend(["using namespace std;", "", "int main() {"])
            lines.extend(body)
            lines.extend(["", "    return 0;", "}"])
        return "\n".join(lines) + ("\n" if lines else "")


def translate_to_javascript(program: Program) -> str:
    return Translator("JavaScript").translate(program)


def translate_to_cpp(program: Program) -> str:
    return Translator("C++").translate(program)


def translate(source: str, target: str = "JavaScript") -> str:
    """Punto de entrada compartido por la interfaz y las pruebas."""
    return Translator(target).translate(parse(tokenize(source)))
