# Compilador Integrado

Proyecto para la asignatura Compiladores. Recibe un programa escrito en Java simplificado, revisa sus tokens, estructura y tipos, y genera código intermedio de tres direcciones y JavaScript. La aplicación permite consultar cada etapa, ver los errores y guardar un HTML para ejecutar el resultado en el navegador.

El repositorio contiene los fuentes, documentación, ejemplos y pruebas. Los binarios y el ZIP se distribuyen por separado mediante GitHub Releases; no se versionan como archivos del repositorio. Para obtener la aplicación de Windows lista para abrir, descarga el ZIP de la Release y extrae todo su contenido.

Se integraron y adaptaron los proyectos de análisis léxico, sintáctico, semántico y traducción. El código de referencia se conserva en `referencias/`; esos archivos documentan el trabajo previo y no son los módulos que ejecuta la aplicación.

## Herramientas y requisitos

| Herramienta | Para qué se utiliza | Cuándo hace falta |
| --- | --- | --- |
| Windows 10/11 de 64 bits | Ejecutar el programa de Windows incluido | Para usar el `.exe` |
| Python 3.10 o posterior con Tkinter | Aplicación, analizadores y pruebas | Para ejecutar o modificar los fuentes |
| Tkinter y biblioteca estándar de Python | Ventana, archivos y pruebas con `unittest` | Se incluyen con la instalación habitual de Python para Windows con Tcl/Tk |
| Chrome, Edge u otro navegador con JavaScript | Ejecutar el HTML exportado | Para ver la salida del programa traducido |
| Node.js | Ejecutar las pruebas automáticas de JavaScript | Opcional; se necesita para comprobar toda la suite |
| FLEX / WinFlexBison y GCC | Regenerar el analizador desde `flex/lexer.l` | Para usar FLEX desde un clon sin binarios; el ZIP de la Release sí incluye el binario |
| PyInstaller | Crear el ejecutable de Windows | Solo para reconstruir el `.exe` |

Para ejecutar los fuentes no hay que instalar paquetes con `pip`. Se verificó el proyecto con Python 3.12.6, Node.js 22.12.0 y PyInstaller 6.22.3. El ejecutable se probó en el equipo de desarrollo; queda pendiente comprobarlo en otro Windows sin Python instalado.

## Ejecutar desde cero

### Opción 1: ejecutable incluido

1. Extrae **todo** el ZIP mediante «Extraer todo»; no abras el programa desde dentro del archivo comprimido.
2. Entra en `Compilador_Integrado` y abre `dist/Compilador_Integrado.exe`.
3. Pulsa **Cargar ejemplo** y después **1. Analizar y traducir**.
4. Revisa las pestañas de estado, tokens, símbolos, AST y código intermedio. El JavaScript aparece a la derecha.
5. Pulsa **2. Guardar JS + HTML** y elige una carpeta con permiso de escritura.
6. Pulsa **3. Abrir navegador** para ejecutar el programa traducido.

El `.exe` contiene el intérprete de Python, Tk/Tcl, el ejemplo y el lexer FLEX. Está preparado para distribuirse sin una instalación de Python.

### Opción 2: código fuente

Instala Python 3.10 o posterior para Windows con Tcl/Tk y el lanzador `py`. Extrae el ZIP y abre PowerShell dentro de `Compilador_Integrado`, donde está `main.py`:

```powershell
py -3 --version
py -3 main.py
```

También puedes abrir `INICIAR.bat`. Si tu instalación usa `python` en lugar de `py`, ejecuta `python main.py` y sustituye `py -3` por `python` en los demás comandos.

El selector léxico ofrece `auto`, `python` y `flex`. `auto` usa el binario FLEX si está disponible; en caso contrario usa Python y lo indica. Un clon del repositorio funciona con Python sin reconstruir FLEX. La opción `flex` exige reconstruir el binario o utilizar el incluido en el ZIP de la Release. El fuente se escribe directamente en el editor; para probar un archivo de `ejemplos/`, copia su contenido o usa la consola.

## Ejecutar desde la consola

Desde la misma carpeta:

```powershell
py -3 cli.py ejemplos/demo.java --lexer python --symbols --intermediate --out salida_demo
py -3 cli.py ejemplos/valido_completo.java --lexer python --out salida_completa
```

Abre `salida_demo/index.html` o `salida_completa/index.html` para ver la salida. Cada exportación contiene `programa.js`, `index.html` e `intermedio.txt`. Mantén el HTML y el JS en la misma carpeta. La carpeta `ejecucion/` ya incluye una exportación del ejemplo principal.

Con el ejemplo principal deben aparecer estas líneas:

```text
Compilador integrado
30
La condición se cumple
0
1
2
```

## Ejemplos y errores

El [índice de ejemplos](ejemplos/README.md) clasifica los programas válidos y los errores léxicos, sintácticos y semánticos, con su resultado esperado. No se cambiaron sus rutas originales.

```powershell
py -3 cli.py ejemplos/error_lexico.java --lexer python
py -3 cli.py ejemplos/error_sintactico.java --lexer python
py -3 cli.py ejemplos/error_semantico.java --lexer python
py -3 cli.py ejemplos/error_inicializacion.java --lexer python
```

Estos cuatro comandos deben terminar con código de salida `1`: es el resultado esperado para entradas incorrectas. La consola usa `0` para compilación correcta y `2` para problemas de lectura o escritura de archivos. Un error de análisis impide exportar un resultado nuevo; los archivos de exportaciones anteriores permanecen en disco.

## Pruebas automáticas

```powershell
py -3 -m unittest discover -s tests -v
```

Hay 42 pruebas de análisis, tipos, ámbitos, inicialización, código intermedio, traducción, consola, exportación y widgets reales de Tkinter. Para ejecutarlas todas se necesita Python con Tkinter, una sesión gráfica de Windows, Node.js en el PATH y `flex/mini_lexer.exe`, disponible en el ZIP de la Release o reconstruido desde los fuentes. Sin Node o FLEX, sus pruebas específicas aparecen como omitidas; eso no equivale a haberlas comprobado.

Las evidencias de la revisión están en `evidencias/`. La comprobación del ZIP extraído se registra junto al paquete, en `entrega/VERIFICACION_ENTREGA.json` y `entrega/pruebas-paquete.txt`.

## Reconstruir las herramientas

Para reconstruir el ejecutable, instala la dependencia de empaquetado y ejecuta el script:

```powershell
py -3 -m pip install -r requirements-build.txt
.\CREAR_EXE.bat
```

El script ejecuta las pruebas, utiliza `Compilador_Integrado.spec` y comprueba el `.exe` resultante con una autoprueba oculta. La salida queda en `dist/Compilador_Integrado.exe` y los registros en `build/`. No es necesario reconstruirlo para usar el ejecutable entregado.

Si deseas regenerar FLEX, instala WinFlexBison y GCC/MSYS2 y agrega sus comandos al PATH. Ejecuta:

```powershell
$env:Path = (Split-Path (Get-Command gcc).Source) + ';' + $env:Path
win_flex -o flex/lex.yy.c flex/lexer.l
gcc flex/lex.yy.c -o flex/mini_lexer.exe
py -3 cli.py ejemplos/demo.java --lexer flex --out salida_flex
```

`compilar_flex.ps1` automatiza esos pasos y restaura el PATH al terminar. En el equipo de desarrollo la política local bloqueó el `.ps1` sin firma: se comprobaron su sintaxis y los comandos directos, sin cambiar esa política.

## Alcance del lenguaje

Se admiten `int`, `double`, `String`, `boolean`, declaraciones, asignaciones, `System.out.println`, `if/else`, `while`, operadores aritméticos, comparaciones, lógica, paréntesis y comentarios `//`. No se escriben clases ni un método `main` de Java.

Es un lenguaje académico simplificado: no incluye funciones de usuario, arreglos, `for`, concatenación ni comentarios de bloque. La división `/` produce `double` y `%` requiere dos `int`. Se exige inicializar antes de leer; el análisis de inicialización es conservador. No se comprueban rangos, división por cero ni terminación de ciclos.

La [documentación técnica](DOCUMENTACION_TECNICA.md) explica las etapas. La [auditoría](AUDITORIA_FINAL.md) conserva la revisión de requisitos y el [guion](GUION_DEMOSTRACION.md) sirve para presentar el proyecto.

## Preparar de nuevo el ZIP

```powershell
py -3 crear_entrega.py --verificar
```

Antes de crear el ZIP desde un clon, reconstruye FLEX con los comandos anteriores. Si quieres incluir la aplicación de Windows, ejecuta también `CREAR_EXE.bat`. El script usa una lista explícita de archivos, comprueba el límite de **20.000.000 bytes**, verifica integridad y hashes, y prueba el proyecto después de extraerlo en una carpeta temporal. Si el paquete completo supera el límite, genera uno de fuentes y conserva el `.exe` en `dist/` para su distribución separada mediante GitHub Releases. No sube nada a Internet.

El ZIP, el inventario completo con tamaños y el informe de verificación quedan en `entrega/`. Dentro del ZIP se incluye `MANIFIESTO_SHA256.txt`. Las cachés y los temporales de compilación no se empaquetan y no se eliminan del proyecto de trabajo.
