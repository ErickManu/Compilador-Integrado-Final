"""Prepara y verifica el ZIP de entrega sin modificar los fuentes ni publicar."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIMIT = 20_000_000  # Limite decimal, mas estricto que 20 MiB.
PREFIX = 'Compilador_Integrado/'
ROOT_FILES = (
    '.gitignore', 'README.md', 'DOCUMENTACION_TECNICA.md', 'AUDITORIA_FINAL.md',
    'GUION_DEMOSTRACION.md', 'requirements-build.txt', 'INICIAR.bat',
    'CREAR_EXE.bat', 'Compilador_Integrado.spec', 'compilar_flex.ps1',
    'main.py', 'cli.py', 'pipeline.py', 'lexer.py', 'parser.py', 'semantic.py',
    'intermediate.py', 'translator.py', 'smoke_check.py', 'crear_entrega.py',
    'flex/lexer.l', 'flex/lex.yy.c', 'flex/mini_lexer.exe',
    'ejecucion/index.html', 'ejecucion/programa.js', 'ejecucion/intermedio.txt',
    'evidencias/README.md', 'evidencias/verificacion-compilacion.txt',
    'evidencias/smoke-exe.json',
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def collect_files():
    paths = {ROOT / name for name in ROOT_FILES}
    for folder, extensions in (
        ('ejemplos', {'.java', '.md'}),
        ('tests', {'.py'}),
        ('referencias', {'.py', '.md'}),
    ):
        paths.update(path for path in (ROOT / folder).rglob('*')
                     if path.is_file() and path.suffix in extensions
                     and '__pycache__' not in path.parts)
    for path in paths:
        if not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f'Falta un archivo de entrega o esta fuera del proyecto: {path}')
    return {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in sorted(paths)}


def write_zip(path, files):
    manifest = '# SHA-256 de todos los archivos del paquete excepto este manifiesto.\n'
    manifest += ''.join(f'{sha256(data)}  {name}\n' for name, data in sorted(files.items()))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(PREFIX + name, data)
        archive.writestr(PREFIX + 'MANIFIESTO_SHA256.txt', manifest.encode('utf-8'))


def check_archive(path, expected):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('El ZIP no supera la comprobacion CRC')
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Hay rutas duplicadas en el ZIP')
        wanted = {PREFIX + name for name in expected} | {PREFIX + 'MANIFIESTO_SHA256.txt'}
        if set(names) != wanted:
            raise ValueError('El contenido del ZIP no coincide con la lista de entrega')
        for name in names:
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts or not name.startswith(PREFIX):
                raise ValueError(f'Ruta invalida: {name}')
        manifest = archive.read(PREFIX + 'MANIFIESTO_SHA256.txt').decode('utf-8')
        recorded = {}
        for line in manifest.splitlines():
            if not line.startswith('#'):
                digest, name = line.split('  ', 1)
                recorded[name] = digest
        if set(recorded) != set(expected):
            raise ValueError('El manifiesto esta incompleto')
        for name, data in expected.items():
            actual = archive.read(PREFIX + name)
            if sha256(actual) != recorded[name] or actual != data:
                raise ValueError(f'El archivo no coincide con el fuente: {name}')
        return [dict(path=item.filename, bytes=item.file_size, compressed_bytes=item.compress_size)
                for item in archive.infolist()]


def check_extracted(archive_path, work, output, includes_exe):
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(work)
    project = work / 'Compilador_Integrado'
    # Evita usar modulos o un lexer externo que no pertenezcan al paquete.
    environment = dict(os.environ, PYTHONIOENCODING='utf-8')
    environment.pop('PYTHONPATH', None)
    environment.pop('MINICOMPILADOR_FLEX_PATH', None)
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                           cwd=project, env=environment, capture_output=True,
                           text=True, encoding='utf-8', timeout=120)
    log = tests.stdout + tests.stderr
    (output / 'pruebas-paquete.txt').write_text(log, encoding='utf-8')
    count = re.search(r'Ran (\d+) tests?', log)
    skipped = re.search(r'skipped=(\d+)', log)
    result = {'source_tests': {'exit_code': tests.returncode,
                              'run': int(count[1]) if count else None,
                              'skipped': int(skipped[1]) if skipped else 0,
                              'ok': tests.returncode == 0 and count is not None}}
    if tests.returncode != 0:
        result['ok'] = False
        return result
    if includes_exe and os.name == 'nt':
        report_path = work / 'smoke-exe-extraido.json'
        run = subprocess.run([str(project / 'dist' / 'Compilador_Integrado.exe'),
                              '--self-test', '--report', str(report_path)],
                             cwd=project, env=environment, capture_output=True, timeout=60,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        smoke = json.loads(report_path.read_text(encoding='utf-8')) if report_path.is_file() else {}
        result['executable'] = dict(smoke, exit_code=run.returncode)
        result['ok'] = bool(result['source_tests']['ok'] and run.returncode == 0
                            and smoke.get('ok') and smoke.get('frozen'))
    else:
        result['executable'] = {'tested': False, 'reason': 'No hay exe incluido o no es Windows'}
        result['ok'] = result['source_tests']['ok']
    return result


def main():
    parser = argparse.ArgumentParser(description='Preparar ZIP universitario de hasta 20 MB')
    parser.add_argument('--verificar', action='store_true',
                        help='Probar los fuentes extraidos y el exe incluido en Windows')
    args = parser.parse_args()
    output = ROOT / 'entrega'
    output.mkdir(exist_ok=True)
    files = collect_files()
    executable = ROOT / 'dist' / 'Compilador_Integrado.exe'
    includes_exe = executable.is_file()
    if includes_exe:
        files['dist/Compilador_Integrado.exe'] = executable.read_bytes()
    # Solo esta carpeta temporal, creada dentro de entrega/, se retira al salir.
    with tempfile.TemporaryDirectory(prefix='verificacion_', dir=output) as temporary:
        work = Path(temporary).resolve()
        if not work.is_relative_to(output.resolve()):
            raise ValueError('La carpeta temporal no pertenece al destino de entrega')
        candidate = work / 'paquete.zip'
        write_zip(candidate, files)
        if candidate.stat().st_size > LIMIT and includes_exe:
            files.pop('dist/Compilador_Integrado.exe')
            includes_exe = False
            write_zip(candidate, files)
        if candidate.stat().st_size > LIMIT:
            raise ValueError('Incluso el ZIP de fuentes supera los 20.000.000 bytes')
        inventory = check_archive(candidate, files)
        name = ('Compilador_Integrado_Entrega_Final.zip' if includes_exe
                else 'Compilador_Integrado_Codigo_Fuente.zip')
        final = output / name
        shutil.copyfile(candidate, final)
        report = {'zip': name, 'bytes': final.stat().st_size, 'limit_bytes': LIMIT,
                  'under_limit': final.stat().st_size <= LIMIT,
                  'sha256': sha256(final.read_bytes()), 'file_count': len(inventory),
                  'includes_windows_executable': includes_exe,
                  'crc_and_manifest': 'correctos', 'files': inventory}
        if args.verificar:
            report['extracted_verification'] = check_extracted(final, work, output, includes_exe)
        else:
            report['extracted_verification'] = {'ok': None, 'reason': 'No se solicito --verificar'}
        (output / 'VERIFICACION_ENTREGA.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        text = [f'ZIP: {name}', f'Tamano: {report["bytes"]} bytes',
                f'Limite: {LIMIT} bytes', f'SHA-256: {report["sha256"]}',
                f'Archivos: {len(inventory)}', f'Incluye ejecutable Windows: {includes_exe}',
                'CRC, manifiesto y comparacion con originales: correctos',
                f'Verificacion extraida: {report["extracted_verification"]}',
                '', 'Bytes originales | Bytes comprimidos | Ruta dentro del ZIP']
        text.extend(f'{item["bytes"]:>12} | {item["compressed_bytes"]:>16} | {item["path"]}'
                    for item in inventory)
        (output / 'CONTENIDO_ZIP.txt').write_text('\n'.join(text) + '\n', encoding='utf-8')
    print(f'ZIP: {final}')
    print(f'Tamano: {report["bytes"]} bytes ({report["bytes"] / 1_000_000:.2f} MB)')
    print(f'Archivos: {report["file_count"]}; incluye exe: {includes_exe}')
    print('Inventario:', output / 'CONTENIDO_ZIP.txt')
    if args.verificar and not report['extracted_verification']['ok']:
        print('La verificacion fallo. Revisa VERIFICACION_ENTREGA.json y pruebas-paquete.txt.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
