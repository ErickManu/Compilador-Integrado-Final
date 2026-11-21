"""Código de tres direcciones desde el AST validado, con ámbitos y cortocircuito."""
import json
from dataclasses import dataclass

from parser import (Assignment, BinaryExpression, Identifier, IfStatement, Literal,
                    PrintStatement, UnaryExpression, VariableDeclaration, WhileStatement)


@dataclass(frozen=True)
class Instruction:
    op: str
    arg1: str = ''
    arg2: str = ''
    result: str = ''

    def __str__(self):
        if self.op == 'label':
            return f'{self.result}:'
        if self.op == 'goto':
            return f'goto {self.result}'
        if self.op == 'if_false':
            return f'if_false {self.arg1} goto {self.result}'
        if self.op == 'declare':
            return f'declare {self.arg1} {self.result}'
        if self.op == 'print':
            return f'print {self.arg1}'
        if self.op == '=':
            return f'{self.result} = {self.arg1}'
        if not self.arg2:
            return f'{self.result} = {self.op}{self.arg1}'
        return f'{self.result} = {self.arg1} {self.op} {self.arg2}'


class IntermediateGenerator:
    def __init__(self):
        self.instructions: list[Instruction] = []
        self.scopes = [{}]
        self.scope_names = ['global']
        self.temp_count = self.label_count = self.block_count = 0

    def emit(self, op, arg1='', arg2='', result=''):
        self.instructions.append(Instruction(op, arg1, arg2, result))

    def temp(self):
        self.temp_count += 1
        return f't{self.temp_count}'

    def label(self):
        self.label_count += 1
        return f'L{self.label_count}'

    def lookup(self, name):
        return next(scope[name] for scope in reversed(self.scopes) if name in scope)

    def expression(self, expr):
        if isinstance(expr, Literal):
            return json.dumps(expr.value, ensure_ascii=False) if expr.kind == 'string' else expr.value
        if isinstance(expr, Identifier):
            return self.lookup(expr.name)
        if isinstance(expr, UnaryExpression):
            operand = self.expression(expr.operand)
            result = self.temp()
            self.emit(expr.operator, operand, result=result)
            return result
        if isinstance(expr, BinaryExpression):
            left = self.expression(expr.left)
            result = self.temp()
            if expr.operator in ('&&', '||'):
                # El operando derecho solo se evalúa cuando corresponde.
                end = self.label()
                self.emit('=', left, result=result)
                if expr.operator == '&&':
                    self.emit('if_false', left, result=end)
                else:
                    right_label = self.label()
                    self.emit('if_false', left, result=right_label)
                    self.emit('goto', result=end)
                    self.emit('label', result=right_label)
                right = self.expression(expr.right)
                self.emit('=', right, result=result)
                self.emit('label', result=end)
            else:
                right = self.expression(expr.right)
                self.emit(expr.operator, left, right, result)
            return result
        raise TypeError(type(expr))

    def block(self, statements):
        self.block_count += 1
        self.scopes.append({})
        self.scope_names.append(f'b{self.block_count}')
        self.statements(statements)
        self.scope_names.pop()
        self.scopes.pop()

    def statements(self, statements):
        for stmt in statements:
            if isinstance(stmt, VariableDeclaration):
                storage = f'{stmt.name}@{self.scope_names[-1]}'
                self.scopes[-1][stmt.name] = storage
                self.emit('declare', stmt.variable_type, result=storage)
                if stmt.initializer is not None:
                    self.emit('=', self.expression(stmt.initializer), result=storage)
            elif isinstance(stmt, Assignment):
                self.emit('=', self.expression(stmt.value), result=self.lookup(stmt.name))
            elif isinstance(stmt, PrintStatement):
                self.emit('print', self.expression(stmt.expression))
            elif isinstance(stmt, IfStatement):
                otherwise, end = self.label(), self.label()
                self.emit('if_false', self.expression(stmt.condition), result=otherwise)
                self.block(stmt.then_body)
                if stmt.else_body is not None:
                    self.emit('goto', result=end)
                self.emit('label', result=otherwise)
                if stmt.else_body is not None:
                    self.block(stmt.else_body)
                    self.emit('label', result=end)
            elif isinstance(stmt, WhileStatement):
                start, end = self.label(), self.label()
                self.emit('label', result=start)
                self.emit('if_false', self.expression(stmt.condition), result=end)
                self.block(stmt.body)
                self.emit('goto', result=start)
                self.emit('label', result=end)
            else:
                raise TypeError(type(stmt))


def generate_intermediate(program) -> list[Instruction]:
    generator = IntermediateGenerator()
    generator.statements(program.statements)
    return generator.instructions
