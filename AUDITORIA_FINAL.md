# Revisión de entrega — Compilador Integrado

Fecha: 20/11/2026. Se trabajó sobre el proyecto existente. Se conservaron la ventana Tkinter, los botones de análisis/guardado/navegador, los lexers Python y FLEX, las referencias históricas y la exportación JavaScript/HTML. No se creó un proyecto nuevo ni se publicó en GitHub. La carpeta recibida no contiene un repositorio Git.

Nota de entrega: los registros citados en `build/` se conservan en la carpeta de trabajo. El ZIP incluye sus copias en `evidencias/verificacion-compilacion.txt` y `evidencias/smoke-exe.json`, sin los temporales de compilación. Las instrucciones actuales están en `README.md`, el índice de ejemplos en `ejemplos/README.md` y la explicación de las etapas en `DOCUMENTACION_TECNICA.md`.

## Diagnóstico inicial, antes de corregir

| # | Requisito | Estado inicial | Archivos y comprobación inicial |
| --- | --- | --- | --- |
| 1 | Analizador léxico | Implementado | `lexer.py`, `flex/lexer.l`, `pipeline.py`. Se analizó el ejemplo con ambos backends; FLEX rechazó `@` y un escape inválido. |
| 2 | Analizador sintáctico | Implementado | `parser.py`. AST y descenso recursivo; pasó la prueba de punto y coma faltante. |
| 3 | Analizador semántico | Incompleto | `semantic.py`. Tipos y ámbitos funcionaban en las pruebas, pero `int x = x + 1;` se aceptaba y Node fallaba con ReferenceError; una lectura sin inicializar producía undefined. |
| 4 | Generación y vista de símbolos | Implementado | `semantic.py`, `main.py`. Nombre, tipo, línea y ámbito; prueba de ámbitos anidados aprobada. La vista con errores semánticos no conservaba los símbolos parciales. |
| 5 | Código intermedio visible | Faltante | No existían generador ni pestaña de tres direcciones. |
| 6 | Lenguaje existente a JavaScript | Incompleto | `translator.py`. El ejemplo se ejecutaba, pero se aceptaba código que fallaba por inicialización. Se confirmó después otro fallo de zona temporal muerta al ocultar una variable externa. |
| 7 | Aplicación única | Implementado | `main.py`, `pipeline.py`, `cli.py`. Integración existente; quedaba verificar la ventana y el paquete en ejecución. |
| 8 | Resultados y errores por etapa | Incompleto | `main.py`, `pipeline.py`. Mostraba el error y los tokens si existían, pero faltaban resultados parciales y estado explícito de etapas no ejecutadas. |
| 9 | JavaScript y HTML ejecutables | Implementado | `pipeline.export_browser()`, `main.py`. Se creaban ambos archivos y Node ejecutaba el ejemplo. |
| 10 | Creación del ejecutable Windows | Incompleto | Había `.spec` y un `.exe` anterior; no existía `CREAR_EXE.bat` ni evidencia de una construcción actual. |

La suite inicial tenía 16 pruebas: 15 aprobadas y una fallida por decodificar la salida UTF-8 de Node con la codificación predeterminada de Windows. No se modificó la salida esperada para ocultar ese fallo: se indicó `encoding='utf-8'` al leerla.

## Estado final y evidencia

Todos los requisitos están implementados dentro del lenguaje simplificado documentado en `README.md`; la verificación del ejecutable corresponde a este equipo Windows, no a otro equipo limpio.

| # | Estado final | Archivos principales | Pruebas y evidencia |
| --- | --- | --- | --- |
| 1 | Implementado | `lexer.py`, `flex/lexer.l`, `flex/lex.yy.c`, `flex/mini_lexer.exe` | Regeneración real con WinFlexBison/GCC; `FlexTests` compara tokens, columnas Unicode, JS e intermedio y rechaza entradas inválidas. |
| 2 | Implementado | `parser.py`, `main.py` | Pruebas de precedencia, unarios, bloques, AST visible, errores de estructura y anidación excesiva. |
| 3 | Implementado | `semantic.py` | Tipos, variables no declaradas, duplicados, ámbitos, condiciones, inicialización propia, uso antes de inicializar y unión de estados de ambas ramas. |
| 4 | Implementado | `semantic.py`, `main.py`, `cli.py` | Pruebas de símbolos y ámbitos; widgets reales muestran cinco símbolos del ejemplo y conservan símbolos parciales en errores semánticos. |
| 5 | Implementado | `intermediate.py`, `pipeline.py`, `main.py`, `cli.py` | `IntermediateTests` ejecuta las instrucciones con un intérprete de pruebas: precedencia, saltos, ciclos anidados, ámbitos, unarios y cortocircuito. Vista inspeccionada en el `.exe`; exporta `intermedio.txt`. |
| 6 | Implementado | `translator.py`, `semantic.py` | Node ejecuta el ejemplo completo, Unicode, escapes, ceros iniciales, operadores y variables ocultadas. JS y tres direcciones coinciden en los resultados de ámbitos. |
| 7 | Implementado | `main.py`, `pipeline.py` | Cinco pruebas con widgets reales, autoprueba del paquete congelado y comprobación visual del ejecutable. |
| 8 | Implementado | `lexer.py`, `pipeline.py`, `main.py`, `cli.py` | Estado CORRECTO/ERROR/NO EJECUTADO por etapa, posiciones, errores semánticos múltiples y resultados parciales. Editar el fuente limpia resultados y bloquea guardado/ejecución anteriores. |
| 9 | Implementado | `pipeline.py`, `main.py`, `ejecucion/` | Exportación de JS/HTML/intermedio, ejecución real en Node, scripts del HTML con DOM mínimo y salida del ejemplo observada en Microsoft Edge. |
| 10 | Implementado | `CREAR_EXE.bat`, `Compilador_Integrado.spec`, `smoke_check.py` | Construcción real con PyInstaller y autoprueba del `.exe`, incluidos Python, FLEX y Tkinter. Resultados en `build/verificacion-final.txt` y `build/smoke-exe.json`. |

## Cambios realizados

- Se añadió `intermediate.py`: instrucciones de tres direcciones, temporales, almacenamiento por ámbito, etiquetas, saltos y cortocircuito. La condición de `while` se vuelve a evaluar en cada vuelta. JS y código intermedio se generan a partir del mismo AST validado; JS no se genera leyendo el texto intermedio.
- Se añadieron pestañas de AST y código intermedio a la ventana existente. Los errores conservan la información de etapas anteriores y las etapas posteriores aparecen como no ejecutadas.
- Se añadió inicialización definida al análisis semántico. Ambas ramas de `if/else` deben asignar para garantizar inicialización al salir; un ciclo puede no ejecutarse. Una variable local oculta a la externa desde su propia declaración, por lo que una inicialización como `int x = x;` se rechaza.
- Se corrigió la traducción de variables locales que ocultan otras: se usan nombres JS como `$x_1`, imposibles de colisionar con identificadores fuente. Esto evita que la zona temporal muerta de `let` intercepte lecturas previas de la variable externa. Los símbolos conservan los nombres originales.
- Se corrigió el cómputo de columnas UTF-8 en FLEX y se excluyeron caracteres de control de sus cadenas. Se regeneraron el C y el binario; se validan también los literales devueltos por el proceso externo.
- Se conservan `programa.js` e `index.html` y se añade `intermedio.txt`. Se muestran errores de lectura/escritura sin una excepción sin manejar en los casos probados.
- Se añadió `CREAR_EXE.bat`: comprueba Python y PyInstaller, ejecuta pruebas, construye con el `.spec` y verifica el ejecutable. El `.spec` empaqueta los ejemplos y el lexer FLEX disponible. La autoprueba escribe JSON, adecuado para un ejecutable sin consola.
- Se actualizó `compilar_flex.ps1` para priorizar las DLL del propio GCC sin modificar permanentemente el PATH. Se actualizó la documentación y se añadieron `valido_completo.java` y `error_inicializacion.java`; se conservaron los ejemplos previos.

## Pruebas ejecutadas

1. `python -m unittest discover -s tests -v`: suite final de **42 pruebas, todas aprobadas, sin omisiones**. Incluye `test_pipeline.py`, `test_execution.py`, `test_cli.py` y `test_ui.py`.
2. `win_flex -o flex/lex.yy.c flex/lexer.l` y `gcc flex/lex.yy.c -o flex/mini_lexer.exe`: ambos terminaron con código 0. GCC requirió anteponer su directorio al PATH del proceso; sin ello terminaba con código 1 sin diagnóstico.
3. `python cli.py ejemplos/demo.java --lexer flex --out ejecucion --symbols --intermediate`: terminó con código 0; generó JS, HTML e intermedio y mostró cinco símbolos. Las pruebas de CLI verifican códigos 1 para errores del lenguaje y 2 para fallos de archivos, sin exportar sobre análisis fallidos.
4. `CREAR_EXE.bat`: construcción final con PyInstaller 6.22.3 y Python 3.12.6. Ejecuta la suite completa y verifica el `.exe` actualizado. El registro completo se conserva en `build/verificacion-final.txt`; `build/smoke-exe.json` debe indicar `ok: true` y `frozen: true` para esta construcción.
5. Comprobación visual del ejecutable: abrió la interfaz existente; el ejemplo mostró cinco etapas correctas, FLEX externo, 99 tokens y cinco variables. Se inspeccionó la nueva pestaña Código intermedio. La autoprueba vuelve a comprobar los widgets desde la construcción final.
6. `ejecucion/index.html` abierto en Microsoft Edge: salida observada `Compilador integrado`, `30`, `La condición se cumple`, `0`, `1`, `2`, sin error visible. Las pruebas de Node verifican además el contenido exportado y la captura mediante `textContent`.

## Límites y pendientes

- Falta probar el ejecutable en un segundo Windows sin Python ni las herramientas de desarrollo instaladas. La construcción, sus recursos y los dos lexers sí se ejecutaron en este equipo.
- La política de PowerShell de este equipo impidió ejecutar `compilar_flex.ps1` porque no está firmado. Se validó su sintaxis y se ejecutaron los comandos directos de compilación; no se cambió la política. `CREAR_EXE.bat` sí fue ejecutado.
- El lenguaje continúa siendo el subconjunto existente: no Java completo. Se conservó `/` como operación `double`, `%` entre `int` y comparación de cadenas por valor. No hay clases, métodos, arreglos, `for`, concatenación ni comentarios de bloque. No se comprueban rangos, divisiones por cero ni terminación de ciclos. La inicialización definida es conservadora.
- El parser y el lexer informan el primer error; el semántico puede reunir varios. Una entrada excesivamente anidada se informa como error de etapa.
- No hay archivos publicados ni cambios enviados a GitHub. No se eliminaron archivos fuente, referencias ni recursos necesarios.
