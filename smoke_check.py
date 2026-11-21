"""Autoprueba del paquete congelado. Escribe JSON porque el .exe no tiene consola."""
import argparse
import json
import sys
import tempfile
from pathlib import Path

from pipeline import CompilationError, compile_source, export_browser, find_flex


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True)
    args = parser.parse_args(argv)
    report = {'ok': False, 'frozen': bool(getattr(sys, 'frozen', False)), 'checks': []}
    try:
        source = (Path(__file__).resolve().parent / 'ejemplos' / 'demo.java').read_text(encoding='utf-8')
        backends = ['python'] + (['flex'] if find_flex() else [])
        for backend in backends:
            result = compile_source(source, backend)
            assert result.tokens and result.symbols and result.instructions and result.javascript
            with tempfile.TemporaryDirectory() as folder:
                js, html = export_browser(result, Path(folder))
                assert js.is_file() and html.is_file() and (Path(folder) / 'intermedio.txt').is_file()
            for invalid, phase in (('@', 'léxico'), ('int x =', 'sintáctico'),
                                   ('int x = "mal";', 'semántico')):
                try:
                    compile_source(invalid, backend)
                except CompilationError as error:
                    assert error.stage.startswith(phase), str(error)
                else:
                    raise AssertionError(f'{backend}: se aceptó {invalid!r}')
            report['checks'].append(f'{backend}: análisis, símbolos, intermedio, JS, exportación y errores')
        # También comprueba Tk/Tcl y los widgets desde los recursos empaquetados.
        import tkinter as tk
        from main import App
        root = tk.Tk()
        root.withdraw()
        try:
            app = App(root)
            root.update()
            app.compile()
            root.update()
            assert app.result is not None
            assert app.intermediate.get('1.0', 'end-1c') == app.result.intermediate
            assert app.symbols.get_children() and app.tokens.get_children()
            report['checks'].append('Tkinter: ventana, análisis y vistas integradas')
        finally:
            root.destroy()
        report['ok'] = True
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
