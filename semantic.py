"""Comprobación semántica adaptada del proyecto Analizador Semántico a
los nodos AST del Traductor de Código. Sin ejecutar el programa.
"""
from dataclasses import dataclass
from lexer import Token
from parser import (Assignment, BinaryExpression, Identifier, IfStatement,
                    Literal, PrintStatement, UnaryExpression,
                    VariableDeclaration, WhileStatement)

# JavaScript reservado: no permitir nombres que harían que la salida JS falle.
JS_RESERVED = frozenset({
    'await', 'break', 'case', 'catch', 'class', 'const', 'continue',
    'debugger', 'default', 'delete', 'do', 'enum', 'export', 'extends',
    'finally', 'for', 'function', 'import', 'in', 'instanceof', 'let',
    'new', 'return', 'super', 'switch', 'this', 'throw', 'try', 'typeof',
    'var', 'void', 'with', 'yield', 'implements', 'interface', 'package',
    'private', 'protected', 'public', 'static', 'null', 'undefined',
    'console', 'window', 'document', 'eval', 'arguments'
})


@dataclass
class Symbol:
    name: str
    data_type: str
    line: int
    scope: str


class SemanticAnalyzer:
    """Revisa declaraciones, ámbitos, operaciones y tipos.

    Comprueba inicialización definida: ambas ramas deben asignar una variable
    para garantizar su valor al salir de un if. Un while puede no ejecutarse.
    """
    def __init__(self):
        self.errors: list[str] = []
        self.symbols: list[Symbol] = []
        self.scopes: list[dict[str, Symbol]] = []
        self.scope_names: list[str] = []
        self.block_number = 0
        self.initialized: set[int] = set()

    def analyze(self, program) -> list[str]:
        self.errors, self.symbols = [], []
        self.scopes, self.scope_names = [{}], ['global']
        self.block_number = 0
        self.initialized = set()
        for stmt in program.statements:
            self.visit(stmt)
        return self.errors

    def error(self, token: Token | None, message: str):
        line = token.line if token else '?'
        col = token.column if token else '?'
        self.errors.append(f'Línea {line}, columna {col}: {message}')

    def lookup(self, name: str, token: Token | None) -> Symbol | None:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        self.error(token, f"La variable '{name}' no ha sido declarada.")
        return None

    @staticmethod
    def compatible(dest: str, src: str | None) -> bool:
        return src is None or dest == src or (dest == 'double' and src == 'int')

    def check_assignment(self, symbol: Symbol, value_type: str | None, token):
        if not self.compatible(symbol.data_type, value_type):
            self.error(token, f"No se puede asignar un valor de tipo {value_type} "
                              f"a '{symbol.name}' de tipo {symbol.data_type}.")

    def block(self, statements):
        self.block_number += 1
        self.scopes.append({})
        self.scope_names.append(f'bloque {self.block_number}')
        try:
            for statement in statements:
                self.visit(statement)
        finally:
            self.initialized.difference_update(id(symbol) for symbol in self.scopes[-1].values())
            self.scopes.pop()
            self.scope_names.pop()

    def visit(self, statement):
        if isinstance(statement, VariableDeclaration):
            name, token = statement.name, statement.token
            if name in JS_RESERVED:
                self.error(token, f"'{name}' es un identificador no permitido en JavaScript.")
            if name in self.scopes[-1]:
                self.error(token, f"La variable '{name}' ya fue declarada en este ámbito.")
                if statement.initializer is not None:
                    self.expression_type(statement.initializer)
                return
            symbol = Symbol(name, statement.variable_type, token.line if token else 0,
                            self.scope_names[-1])
            self.scopes[-1][name] = symbol
            self.symbols.append(symbol)
            if statement.initializer is not None:
                self.check_assignment(symbol, self.expression_type(statement.initializer), token)
                self.initialized.add(id(symbol))
        elif isinstance(statement, Assignment):
            symbol = self.lookup(statement.name, statement.token)
            rhs = self.expression_type(statement.value)
            if symbol:
                self.check_assignment(symbol, rhs, statement.token)
                self.initialized.add(id(symbol))
        elif isinstance(statement, PrintStatement):
            self.expression_type(statement.expression)
        elif isinstance(statement, IfStatement):
            cond = self.expression_type(statement.condition)
            if cond is not None and cond != 'boolean':
                self.error(statement.token, f'La condición de if debe ser boolean, no {cond}.')
            before = self.initialized.copy()
            self.block(statement.then_body)
            after_then = self.initialized.copy()
            self.initialized = before.copy()
            if statement.else_body is not None:
                self.block(statement.else_body)
            self.initialized.intersection_update(after_then)
        elif isinstance(statement, WhileStatement):
            cond = self.expression_type(statement.condition)
            if cond is not None and cond != 'boolean':
                self.error(statement.token, f'La condición de while debe ser boolean, no {cond}.')
            before = self.initialized.copy()
            self.block(statement.body)
            self.initialized = before
        else:
            raise TypeError(type(statement))

    def expression_type(self, expr) -> str | None:
        if isinstance(expr, Literal):
            return ('String' if expr.kind == 'string' else 'boolean' if expr.kind == 'boolean'
                    else 'double' if '.' in expr.value else 'int')
        if isinstance(expr, Identifier):
            symbol = self.lookup(expr.name, expr.token)
            if symbol and id(symbol) not in self.initialized:
                self.error(expr.token, f"La variable '{expr.name}' se usa sin inicializar.")
            return symbol.data_type if symbol else None
        if isinstance(expr, UnaryExpression):
            kind = self.expression_type(expr.operand)
            if kind is None:
                return None
            if expr.operator == '!' and kind == 'boolean':
                return 'boolean'
            if expr.operator in ('+', '-') and kind in ('int', 'double'):
                return kind
            self.error(expr.token, f"Operador '{expr.operator}' incompatible con {kind}.")
            return None
        if isinstance(expr, BinaryExpression):
            left, right = self.expression_type(expr.left), self.expression_type(expr.right)
            if left is None or right is None:
                return None
            op = expr.operator
            numeric = left in ('int', 'double') and right in ('int', 'double')
            if op in ('+', '-', '*', '/'):
                if numeric:
                    return 'double' if op == '/' or 'double' in (left, right) else 'int'
                reason = 'requiere operandos numéricos'
            elif op == '%':
                if left == right == 'int':
                    return 'int'
                reason = 'requiere dos valores int'
            elif op in ('<', '>', '<=', '>='):
                if numeric:
                    return 'boolean'
                reason = 'requiere operandos numéricos'
            elif op in ('==', '!='):
                if left == right or numeric:
                    return 'boolean'
                reason = 'compara tipos incompatibles'
            elif op in ('&&', '||'):
                if left == right == 'boolean':
                    return 'boolean'
                reason = 'requiere dos boolean'
            else:
                raise ValueError(f'Operador desconocido: {op}')
            self.error(expr.token, f"'{op}' {reason} (recibió {left} y {right}).")
            return None
        raise TypeError(type(expr))
