"""Integración de widgets Tk reales, sin abrir navegador ni diálogos interactivos."""
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from main import App


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = App(self.root)
        self.app.backend.set('python')
        self.root.update()

    def source(self, text):
        self.app.source.delete('1.0', 'end')
        self.app.source.insert('1.0', text)
        self.root.update()

    def test_compile_populates_all_views(self):
        self.app.compile()
        self.root.update()
        self.assertIsNotNone(self.app.result)
        self.assertTrue(self.app.tokens.get_children())
        self.assertEqual(len(self.app.symbols.get_children()), 5)
        self.assertIn('Program(', self.app.ast.get('1.0', 'end'))
        self.assertIn('if_false', self.app.intermediate.get('1.0', 'end'))
        self.assertIn('JavaScript: CORRECTO', self.app.log.get('1.0', 'end'))

    def test_errors_preserve_partial_analysis_and_clear_generated_code(self):
        self.app.compile()
        self.source('int x = "mal";')
        self.app.compile()
        self.assertIsNone(self.app.result)
        self.assertEqual(self.app.output.get('1.0', 'end-1c'), '')
        self.assertEqual(self.app.intermediate.get('1.0', 'end-1c'), '')
        self.assertTrue(self.app.symbols.get_children())
        self.assertIn('Program(', self.app.ast.get('1.0', 'end'))
        self.assertIn('Código intermedio: NO EJECUTADO', self.app.log.get('1.0', 'end'))
        with patch('main.messagebox.showwarning') as warning:
            self.app.save()
            self.app.open_browser()
        self.assertEqual(warning.call_count, 2)

    def test_edit_and_load_clear_stale_results(self):
        self.app.compile()
        self.source('int x = 1;')
        self.assertIsNone(self.app.result)
        self.assertEqual(self.app.output.get('1.0', 'end-1c'), '')
        self.assertFalse(self.app.symbols.get_children())
        self.app.compile()
        self.app.load_example()
        self.assertIsNone(self.app.result)
        self.assertEqual(self.app.intermediate.get('1.0', 'end-1c'), '')
        self.app.clear()
        self.assertEqual(self.app.source.get('1.0', 'end-1c'), '')

    def test_save_and_browser_target(self):
        self.app.compile()
        with tempfile.TemporaryDirectory() as folder:
            with patch('main.filedialog.askdirectory', return_value=folder), patch('main.messagebox.showinfo'):
                self.app.save()
            for name in ('programa.js', 'index.html', 'intermedio.txt'):
                self.assertTrue((Path(folder) / name).is_file())
            with patch('main.webbrowser.open') as browser:
                self.app.open_browser()
            browser.assert_called_once_with((Path(folder) / 'index.html').resolve().as_uri())

    def test_export_error_is_visible(self):
        self.app.compile()
        with patch('main.filedialog.askdirectory', return_value='destino'), \
             patch('main.export_browser', side_effect=OSError('sin permiso')), \
             patch('main.messagebox.showerror') as error:
            self.app.save()
        error.assert_called_once()
        self.assertIsNone(self.app.folder)
