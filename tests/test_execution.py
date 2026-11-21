"""Comprueba el comportamiento del JS y del código de tres direcciones.

El intérprete de pruebas ejecuta las instrucciones, incluidos los saltos; así
se contrastan resultados observables y no solo el formato del generador.
"""
import json
import operator
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from pipeline import CompilationError, compile_source, export_browser, find_flex

ROOT = Path(__file__).resolve().parents[1]
OPS = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv,
       '%': operator.mod, '<': operator.lt, '>': operator.gt, '<=': operator.le,
       '>=': operator.ge, '==': operator.eq, '!=': operator.ne}


def execute_ir(instructions):
    memory, output = {}, []
    labels = {item.result: i for i, item in enumerate(instructions) if item.op == 'label'}

    def value(text):
        if text in memory:
            return memory[text]
        return json.loads(text)

    pc = steps = 0
    while pc < len(instructions):
        steps += 1
        if steps > 10000:
            raise AssertionError('El código intermedio no termina dentro del límite de la prueba')
        item = instructions[pc]
        if item.op == 'goto':
            pc = labels[item.result]
            continue
        if item.op == 'if_false' and not value(item.arg1):
            pc = labels[item.result]
            continue
        if item.op == 'print':
            output.append(value(item.arg1))
        elif item.op == '=':
            memory[item.result] = value(item.arg1)
        elif item.op in OPS:
            if item.arg2:
                memory[item.result] = OPS[item.op](value(item.arg1), value(item.arg2))
            else:
                memory[item.result] = (-value(item.arg1) if item.op == '-' else +value(item.arg1))
        elif item.op == '!':
            memory[item.result] = not value(item.arg1)
        elif item.op not in ('declare', 'label', 'if_false'):
            raise AssertionError(f'Instrucción desconocida: {item.op}')
        pc += 1
    return output


class IntermediateTests(unittest.TestCase):
    def test_precedence_branches_scopes_and_loops(self):
        source = (ROOT / 'ejemplos' / 'valido_completo.java').read_text(encoding='utf-8')
        result = compile_source(source, 'python')
        self.assertEqual(execute_ir(result.instructions),
                         ['Compilación válida', 14, 2.5, 7, 0, 1, 2, 4, True])
        self.assertIn('x@global', result.intermediate)
        self.assertIn('x@b3', result.intermediate)

    def test_short_circuit_skips_right_operand(self):
        result = compile_source('boolean a = false && (1 / 0 > 0); '
                                'boolean b = true || (1 / 0 > 0); '
                                'System.out.println(a); System.out.println(b);', 'python')
        self.assertEqual(execute_ir(result.instructions), [False, True])

    def test_both_right_operands_and_nested_logic(self):
        result = compile_source('System.out.println(true && (false || true)); '
                                'System.out.println(false || (true && !true)); '
                                'System.out.println(- -3 + +2);', 'python')
        self.assertEqual(execute_ir(result.instructions), [True, False, 5])

    def test_nested_loop_reinitializes_local_declarations(self):
        result = compile_source('int i = 0; while (i < 2) { int j = 0; '
                                'while (j < 2) { System.out.println(i * 10 + j); j = j + 1; } '
                                'i = i + 1; }', 'python')
        self.assertEqual(execute_ir(result.instructions), [0, 1, 10, 11])

    def test_empty_program(self):
        result = compile_source('', 'python')
        self.assertEqual(result.instructions, [])
        self.assertEqual(result.javascript, '')


@unittest.skipUnless(shutil.which('node'), 'Node.js no instalado: ejecución JS no comprobada')
class JavascriptTests(unittest.TestCase):
    def run_js(self, result):
        cp = subprocess.run(['node', '-e', result.javascript], capture_output=True,
                            text=True, encoding='utf-8', timeout=5, check=True)
        return cp.stdout.splitlines()

    def test_full_example(self):
        for backend in ['python'] + (['flex'] if find_flex() else []):
            with self.subTest(backend=backend):
                result = compile_source((ROOT / 'ejemplos' / 'valido_completo.java').read_text(encoding='utf-8'), backend)
                self.assertEqual(self.run_js(result),
                                 ['Compilación válida', '14', '2.5', '7', '0', '1', '2', '4', 'true'])

    def test_escapes_leading_zeroes_and_unary(self):
        result = compile_source(r'String s = "á\n\"\\"; System.out.println(s); '
                                'System.out.println(007 + - -3); System.out.println(10 - 3 - 2);', 'python')
        self.assertEqual(self.run_js(result), ['á', '"\\', '10', '5'])

    def test_shadowing_preserves_earlier_reads_of_outer_variable(self):
        result = compile_source('int x = 1; if (true) { System.out.println(x); '
                                'int x = 2; x = x + 1; System.out.println(x); '
                                'if (true) { System.out.println(x); int x = 4; System.out.println(x); } '
                                '} System.out.println(x);', 'python')
        self.assertEqual(self.run_js(result), ['1', '3', '3', '4', '1'])
        self.assertEqual(execute_ir(result.instructions), [1, 3, 3, 4, 1])

    def test_browser_html_executes_external_js_and_captures_output(self):
        result = compile_source('System.out.println("Hola <mundo>");', 'python')
        with tempfile.TemporaryDirectory() as temp:
            js, html = export_browser(result, Path(temp))
            self.assertEqual((Path(temp) / 'intermedio.txt').read_text(encoding='utf-8'), result.intermediate + '\n')
            # Ejecuta los scripts reales del HTML con un DOM mínimo para validar
            # el enlace al JS y la escritura segura de la salida como textContent.
            harness = r'''
const fs = require('fs'), vm = require('vm'), path = require('path');
const file = process.argv[1], html = fs.readFileSync(file, 'utf8');
const element = {textContent: ''};
const ctx = vm.createContext({console: {log() {}},
  document: {getElementById(id) {if(id !== 'salida') throw Error(id); return element;}},
  window: {addEventListener() {}}});
for (const match of html.matchAll(/<script(?: src="([^"]+)")?>([\s\S]*?)<\/script>/g)) {
  vm.runInContext(match[1] ? fs.readFileSync(path.join(path.dirname(file), match[1]), 'utf8') : match[2], ctx);
}
process.stdout.write(element.textContent);
'''
            cp = subprocess.run(['node', '-e', harness, str(html)], capture_output=True,
                                text=True, encoding='utf-8', timeout=5, check=True)
            self.assertEqual(cp.stdout, 'Hola <mundo>\n')


@unittest.skipUnless(find_flex(), 'No se encontró binario FLEX: integración FLEX no comprobada')
class FlexTests(unittest.TestCase):
    def test_tokens_match_python_including_unicode_columns(self):
        source = 'String s = "á漢🙂"; int x = 007;\n// comentario\nSystem.out.println(s);'
        python = compile_source(source, 'python')
        flex = compile_source(source, 'flex')
        self.assertEqual(python.tokens, flex.tokens)
        self.assertEqual(python.javascript, flex.javascript)
        self.assertEqual(python.instructions, flex.instructions)

    def test_invalid_inputs_report_correct_phase(self):
        for source, phase in (('@', 'léxico (FLEX)'),
                              (r'String s = "\q";', 'léxico (FLEX)'),
                              ('String s = "a\x01b";', 'léxico (FLEX)'),
                              ('int x = 1', 'sintáctico'),
                              ('int x = "mal";', 'semántico'),
                              ('int x = x;', 'semántico')):
            with self.subTest(source=source), self.assertRaises(CompilationError) as caught:
                compile_source(source, 'flex')
            self.assertEqual(caught.exception.stage, phase)
