"""Consola para ejecutar pruebas y generar el JavaScript sin abrir Tkinter."""
import argparse
import sys
from pathlib import Path
from pipeline import CompilationError, compile_source, export_browser, stage_report


def main():
    parser = argparse.ArgumentParser(description='Compilador académico a JavaScript')
    parser.add_argument('archivo', help='Archivo fuente Java simplificado')
    parser.add_argument('--out', default='ejecucion', help='Carpeta de salida')
    parser.add_argument('--lexer', choices=['auto', 'flex', 'python'], default='auto')
    parser.add_argument('--intermediate', action='store_true', help='Mostrar código de tres direcciones')
    parser.add_argument('--symbols', action='store_true', help='Mostrar tabla de símbolos')
    args = parser.parse_args()
    try:
        result = compile_source(Path(args.archivo).read_text(encoding='utf-8'), args.lexer)
    except (OSError, UnicodeError) as exc:
        print(f'No se pudo leer el archivo: {exc}', file=sys.stderr)
        return 2
    except CompilationError as exc:
        print(stage_report(exc) + '\n\n' + '\n'.join(exc.problems), file=sys.stderr)
        return 1
    try:
        js, html = export_browser(result, Path(args.out))
    except OSError as exc:
        print(f'No se pudo guardar: {exc}', file=sys.stderr)
        return 2
    print(stage_report(result))
    if args.symbols:
        print('\nNombre\tTipo\tLínea\tÁmbito')
        for symbol in result.symbols:
            print(f'{symbol.name}\t{symbol.data_type}\t{symbol.line}\t{symbol.scope}')
    if args.intermediate:
        print('\nCódigo de tres direcciones:\n' + result.intermediate)
    print('Código JavaScript generado:', js.resolve())
    print('Abrir en el navegador:', html.resolve())
    print('Código intermedio guardado:', (html.parent / 'intermedio.txt').resolve())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
