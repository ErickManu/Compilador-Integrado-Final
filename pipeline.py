"""Integración: léxico -> sintáctico -> semántico -> tres direcciones y JS."""
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from lexer import LexerError, Token, tokenize
from parser import ParserError, Program, parse
from semantic import SemanticAnalyzer, Symbol
from translator import translate_to_javascript
from intermediate import Instruction, generate_intermediate

ROOT = Path(__file__).resolve().parent


class CompilationError(Exception):
    def __init__(self, stage: str, problems: list[str], tokens=None,
                 symbols=None, program=None, lexer_used=None):
        super().__init__('; '.join(problems))
        self.stage, self.problems = stage, problems
        self.tokens = tokens or []
        self.symbols = symbols or []
        self.program = program
        self.lexer_used = lexer_used


@dataclass
class Compilation:
    tokens: list[Token]
    program: Program
    symbols: list[Symbol]
    javascript: str
    lexer_used: str
    instructions: list[Instruction] = field(default_factory=list)

    @property
    def intermediate(self) -> str:
        return '\n'.join(str(item) for item in self.instructions)


def stage_report(result: Compilation | CompilationError) -> str:
    """Estado explícito de cada fase, incluyendo las que no se ejecutaron."""
    phases = ('Léxico', 'Sintáctico', 'Semántico', 'Código intermedio', 'JavaScript')
    failed = result.stage.split(' (')[0].casefold() if isinstance(result, CompilationError) else None
    stopped = False
    lines = []
    for phase in phases:
        status = 'NO EJECUTADO' if stopped else 'CORRECTO'
        if phase.casefold() == failed:
            status, stopped = 'ERROR', True
        detail = f' ({result.lexer_used})' if phase == 'Léxico' and result.lexer_used else ''
        lines.append(f'{phase}: {status}{detail}')
    return '\n'.join(lines)


def find_flex():
    env = os.environ.get('MINICOMPILADOR_FLEX_PATH')
    candidates = ([Path(env)] if env else []) + [
        ROOT / 'flex' / 'mini_lexer.exe',
        ROOT / 'flex' / 'mini_lexer',
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def flex_tokenize(source: str, binary: Path):
    try:
        cp = subprocess.run([str(binary)], input=source, text=True,
                            capture_output=True, timeout=8, encoding='utf-8',
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CompilationError('léxico (FLEX)', [f'No se pudo ejecutar FLEX: {exc}']) from exc
    if cp.returncode:
        raise CompilationError('léxico (FLEX)', [f'FLEX devolvió código {cp.returncode}: {cp.stderr[:500]}'])
    tokens = []
    try:
        for item in cp.stdout.splitlines():
            token_type, line, column, json_value = item.split('\t', 3)
            value = json.loads(json_value)
            if not isinstance(value, str) or int(line) < 1 or int(column) < 1:
                raise ValueError('Valor o posición de token inválidos')
            token = Token(token_type, value, int(line), int(column))
            if token.type == 'ERROR':
                raise CompilationError('léxico (FLEX)',
                                       [f'Línea {line}, columna {column}: carácter o literal no reconocido: {value!r}.'],
                                       tokens)
            if token.type == 'STRING_LITERAL':
                # No dejar que un literal inválido del binario llegue al parser.
                json.loads(value)
            tokens.append(token)
    except (ValueError, TypeError) as exc:
        raise CompilationError('léxico (FLEX)', [f'Salida de FLEX inválida: {exc}'], tokens) from exc
    if not tokens or tokens[-1].type != 'EOF':
        raise CompilationError('léxico (FLEX)', ['FLEX no devolvió el token final EOF.'])
    return tokens


def compile_source(source: str, backend: str = 'auto') -> Compilation:
    if backend not in ('auto', 'flex', 'python'):
        raise ValueError('backend debe ser auto, flex o python')
    executable = find_flex() if backend != 'python' else None
    if backend == 'flex' and executable is None:
        raise CompilationError('léxico (FLEX)',
                               ['No se encontró flex/mini_lexer.exe. Compílalo primero usando win_flex y gcc.'])
    if executable:
        tokens = flex_tokenize(source, executable)
        used = 'FLEX (ejecutable externo)'
    else:
        try:
            tokens = tokenize(source)
        except (LexerError, ValueError) as exc:
            raise CompilationError('léxico (Python)', [str(exc)], getattr(exc, 'tokens', []),
                                   lexer_used='Python') from exc
        used = 'Python (alternativo; FLEX no compilado)' if backend == 'auto' else 'Python'
    try:
        program = parse(tokens)
    except (ParserError, RecursionError) as exc:
        message = 'Anidación demasiado profunda.' if isinstance(exc, RecursionError) else str(exc)
        raise CompilationError('sintáctico', [message], tokens, lexer_used=used) from exc
    checker = SemanticAnalyzer()
    try:
        problems = checker.analyze(program)
    except RecursionError as exc:
        raise CompilationError('semántico', ['Anidación demasiado profunda.'], tokens,
                               checker.symbols, program, used) from exc
    if problems:
        raise CompilationError('semántico', problems, tokens, checker.symbols, program, used)
    try:
        instructions = generate_intermediate(program)
    except RecursionError as exc:
        raise CompilationError('código intermedio', ['Anidación demasiado profunda.'], tokens,
                               checker.symbols, program, used) from exc
    try:
        javascript = translate_to_javascript(program)
    except RecursionError as exc:
        raise CompilationError('JavaScript', ['Anidación demasiado profunda.'], tokens,
                               checker.symbols, program, used) from exc
    return Compilation(tokens, program, checker.symbols, javascript, used, instructions)


BROWSER_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Compilador integrado - Ejecución JavaScript</title>
  <style>
    body { font: 16px system-ui, sans-serif; max-width: 760px; margin: 8vh auto;
           padding: 20px; color: #163356; background: white; }
    h1 { color: #135eaa; }
    pre { background: #eff7ff; border: 1px solid #c8e2fa; padding: 20px;
          border-radius: 10px; min-height: 65px; white-space: pre-wrap; }
    small { color: #52677b; }
  </style>
</head>
<body>
  <h1>Ejecución del programa traducido</h1>
  <p>Salida de <code>programa.js</code>:</p>
  <pre id="salida"></pre>
  <small>Puedes abrir F12 → Console para ver la misma salida.</small>
  <script>
    const originalLog = console.log.bind(console);
    console.log = (...args) => {
      originalLog(...args);
      document.getElementById('salida').textContent += args.map(
        x => typeof x === 'object' ? JSON.stringify(x) : String(x)
      ).join(' ') + '\\n';
    };
    window.addEventListener('error', event => {
      document.getElementById('salida').textContent += 'Error: ' + event.message + '\\n';
    });
  </script>
  <script src="programa.js"></script>
</body>
</html>
'''


def export_browser(result: Compilation, folder: Path) -> tuple[Path, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    js = folder / 'programa.js'
    html = folder / 'index.html'
    js.write_text(result.javascript, encoding='utf-8')
    html.write_text(BROWSER_HTML, encoding='utf-8')
    (folder / 'intermedio.txt').write_text(result.intermediate + '\n', encoding='utf-8')
    return js, html
