"""Contrato de consola: archivos exportados, códigos de salida y errores."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConsoleTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'cli.py'), *map(str, args)],
                              cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, timeout=10)

    def test_valid_source_exports_and_displays_results(self):
        with tempfile.TemporaryDirectory() as folder:
            cp = self.run_cli('ejemplos/valido_completo.java', '--lexer', 'python',
                              '--out', folder, '--intermediate', '--symbols')
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn('Código intermedio: CORRECTO', cp.stdout)
            self.assertIn('Nombre\tTipo', cp.stdout)
            self.assertIn('if_false', cp.stdout)
            for name in ('programa.js', 'index.html', 'intermedio.txt'):
                self.assertTrue((Path(folder) / name).is_file())

    def test_invalid_examples_do_not_export(self):
        with tempfile.TemporaryDirectory() as folder:
            for filename, stage in (('error_lexico.java', 'Léxico'),
                                    ('error_sintactico.java', 'Sintáctico'),
                                    ('error_semantico.java', 'Semántico'),
                                    ('error_inicializacion.java', 'Semántico')):
                with self.subTest(filename=filename):
                    cp = self.run_cli(ROOT / 'ejemplos' / filename, '--lexer', 'python', '--out', folder)
                    self.assertEqual(cp.returncode, 1, cp.stderr)
                    self.assertIn(f'{stage}: ERROR', cp.stderr)
                    self.assertEqual(list(Path(folder).iterdir()), [])

    def test_missing_input_and_invalid_output(self):
        with tempfile.TemporaryDirectory() as folder:
            cp = self.run_cli(Path(folder) / 'no_existe.java')
            self.assertEqual(cp.returncode, 2)
            self.assertIn('No se pudo leer', cp.stderr)
            destination = Path(folder) / 'archivo'
            destination.write_text('conservar', encoding='utf-8')
            cp = self.run_cli('ejemplos/demo.java', '--out', destination)
            self.assertEqual(cp.returncode, 2)
            self.assertIn('No se pudo guardar', cp.stderr)
            self.assertEqual(destination.read_text(encoding='utf-8'), 'conservar')
