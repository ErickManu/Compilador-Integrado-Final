"""Regresión de la integración y ejecución JavaScript con UTF-8 explícito."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline import CompilationError, compile_source, export_browser


class PipelineTests(unittest.TestCase):
    def bad(self, source, phase, clue=None):
        with self.assertRaises(CompilationError) as caught:
            compile_source(source, 'python')
        self.assertEqual(caught.exception.stage, phase)
        if clue:
            self.assertIn(clue, str(caught.exception))

    def test_basic_translation(self):
        r = compile_source('int a = 10; int b = 20; System.out.println(a + b);', 'python')
        self.assertIn('console.log((a + b));', r.javascript)
        self.assertEqual([x.name for x in r.symbols], ['a', 'b'])

    def test_example(self):
        source = (Path(__file__).parents[1] / 'ejemplos' / 'demo.java').read_text(encoding='utf-8')
        r = compile_source(source, 'python')
        self.assertIn('while (', r.javascript)
        with tempfile.TemporaryDirectory() as temp:
            js, html = export_browser(r, Path(temp))
            self.assertTrue(js.is_file())
            self.assertIn('src="programa.js"', html.read_text(encoding='utf-8'))
            if shutil.which('node'):
                cp = subprocess.run(['node', str(js)], capture_output=True, text=True,
                                    encoding='utf-8', timeout=5, check=True)
                self.assertEqual(cp.stdout.strip().splitlines(),
                                 ['Compilador integrado', '30', 'La condición se cumple', '0', '1', '2'])

    def test_nested_scope(self):
        r = compile_source('int x = 3; if (true) { int x = 4; System.out.println(x); } System.out.println(x);', 'python')
        self.assertEqual(len(r.symbols), 2)

    def test_unknown_var(self):
        self.bad('System.out.println(inexistente);', 'semántico', 'no ha sido declarada')

    def test_incompatible_type(self):
        self.bad('int edad = "hola";', 'semántico', 'tipo String')

    def test_double_accepts_int(self):
        r = compile_source('double x = 4; System.out.println(x);', 'python')
        self.assertIn('let x = 4;', r.javascript)

    def test_double_to_int_rejected(self):
        self.bad('int x = 3.5;', 'semántico', 'tipo double')

    def test_duplicate_declaration(self):
        self.bad('int x = 3; int x = 4;', 'semántico', 'ya fue declarada')

    def test_out_of_scope(self):
        self.bad('if (true) { int x = 4; } System.out.println(x);', 'semántico', 'no ha sido declarada')

    def test_invalid_boolean_condition(self):
        self.bad('if (3) { int x = 4; }', 'semántico', 'debe ser boolean')

    def test_non_numeric_addition(self):
        self.bad('String s = "Hola"; int x = s + 2;', 'semántico', 'operandos numéricos')

    def test_lexical_invalid(self):
        self.bad('int x = 10; @', 'léxico (Python)', 'Carácter no reconocido')

    def test_syntactic_missing_semicolon(self):
        self.bad('int x = 10', 'sintáctico', "';'")

    def test_js_reserved_name(self):
        self.bad('int let = 3;', 'semántico', 'identificador no permitido')

    def test_comments(self):
        r = compile_source('int n = 2; // ejemplo\nSystem.out.println(n);', 'python')
        self.assertIn('console.log(n);', r.javascript)

    def test_explicit_flex_requires_binary(self):
        # Especificar FLEX no debe fingir que funcionó si falta su .exe.
        with patch('pipeline.find_flex', return_value=None):
            with self.assertRaises(CompilationError) as caught:
                compile_source('int n = 2;', 'flex')
            self.assertEqual(caught.exception.stage, 'léxico (FLEX)')
            self.assertIn('No se encontró', str(caught.exception))

    def test_auto_falls_back_to_python(self):
        with patch('pipeline.find_flex', return_value=None):
            result = compile_source('int x = 2;')
        self.assertIn('Python', result.lexer_used)

    def test_definite_initialization(self):
        for source in (
            'int x; System.out.println(x);',
            'int x = x + 1;',
            'int x; x = x + 1;',
            'int x = 1; if (true) { int x = x; }',
            'int x; if (true) { x = 1; } System.out.println(x);',
            'int x; while (false) { x = 1; } System.out.println(x);',
            'int x; if (true) { x = 1; } else { System.out.println(x); }',
        ):
            with self.subTest(source=source):
                self.bad(source, 'semántico', 'sin inicializar')

    def test_assignment_in_both_branches(self):
        compile_source('int x; if (true) { x = 1; } else { x = 2; } System.out.println(x);', 'python')
        compile_source('int x; x = 2; while (false) { x = x + 1; } System.out.println(x);', 'python')

    def test_more_errors_with_locations(self):
        cases = (
            ('int x = 1;\n@', 'léxico (Python)', 'línea 2, columna 1'),
            ('String s = "sin cierre;', 'léxico (Python)', 'comillas de cierre'),
            (r'String s = "\q";', 'léxico (Python)', 'escape no soportada'),
            ('if (true) { int x = 1;', 'sintáctico', "'}'"),
            ('int x = ;', 'sintáctico', 'Se esperaba un valor'),
            ('else {}', 'sintáctico', 'Se esperaba'),
            ('boolean b = 1 && true;', 'semántico', 'dos boolean'),
            ('boolean b = !1;', 'semántico', 'incompatible'),
            ('int x = 5 / 2;', 'semántico', 'tipo double'),
            ('double x = 2.5 % 2;', 'semántico', 'dos valores int'),
            ('while (2) {}', 'semántico', 'debe ser boolean'),
        )
        for source, phase, clue in cases:
            with self.subTest(source=source):
                self.bad(source, phase, clue)

    def test_partial_results_and_phase_report(self):
        from pipeline import stage_report
        for source, stage in (('int a = 1; @', 'léxico (Python)'),
                              ('int a = 1', 'sintáctico'),
                              ('int a = "mal";', 'semántico')):
            with self.subTest(stage=stage), self.assertRaises(CompilationError) as caught:
                compile_source(source, 'python')
            error = caught.exception
            self.assertEqual(error.stage, stage)
            self.assertTrue(error.tokens)
            self.assertIn('JavaScript: NO EJECUTADO', stage_report(error))
            if stage == 'semántico':
                self.assertEqual(error.symbols[0].name, 'a')
                self.assertIsNotNone(error.program)
                self.assertIn('Sintáctico: CORRECTO', stage_report(error))

    def test_multiple_semantic_errors(self):
        with self.assertRaises(CompilationError) as caught:
            compile_source('int a = "x"; boolean b = 1; System.out.println(z);', 'python')
        self.assertEqual(len(caught.exception.problems), 3)

    def test_deep_nesting_is_reported(self):
        self.bad('int x = ' + '(' * 300 + '1' + ')' * 300 + ';',
                 'sintáctico', 'Anidación demasiado profunda')


if __name__ == '__main__':
    unittest.main()
