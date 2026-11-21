# Documentación técnica

## Organización

`main.py` presenta la ventana Tkinter y `cli.py` ofrece la misma compilación desde consola. Ambos llaman a `compile_source()` en `pipeline.py`:

```text
Fuente → Tokens → AST → Análisis semántico y símbolos
                              ├→ Código de tres direcciones
                              └→ JavaScript → HTML de ejecución
```

Se genera JavaScript desde el AST validado, no mediante sustituciones de texto ni leyendo el listado de código intermedio. El proyecto usa la biblioteca estándar de Python; FLEX funciona como proceso externo.

## Analizador léxico

`lexer.py` reconoce palabras reservadas, identificadores, números, cadenas, operadores y separadores. Cada `Token` contiene tipo, valor, línea y columna, con posiciones desde 1. Admite comentarios `//` y los escapes de cadena documentados en el lenguaje.

`flex/lexer.l` describe el mismo lenguaje en FLEX. WinFlexBison produce `flex/lex.yy.c` y GCC genera `flex/mini_lexer.exe`. El binario recibe el fuente por entrada estándar y devuelve tokens en líneas con tipo, posición y valor JSON. `pipeline.py` interpreta esa salida, comprueba errores y exige el token final `EOF`.

`python` selecciona el lexer Python, `flex` exige el binario y `auto` elige FLEX cuando está presente. La ventana indica qué implementación se utilizó. Las pruebas comparan ambos backends, incluidas las posiciones después de cadenas Unicode.

## Analizador sintáctico

`parser.py` utiliza descenso recursivo. Comprueba declaraciones, asignaciones, impresión, condicionales y ciclos; exige puntos y comas, paréntesis y llaves donde corresponde. Construye un árbol de sintaxis abstracta (AST) con nodos como `VariableDeclaration`, `BinaryExpression`, `IfStatement` y `WhileStatement`.

La precedencia, de mayor a menor, es: paréntesis, unarios, multiplicación/división/módulo, suma/resta, relaciones, igualdad, `&&` y `||`. Los binarios de la misma prioridad se agrupan por la izquierda. Los nodos conservan tokens para localizar errores. La pestaña AST permite inspeccionar el árbol reconocido.

## Analizador semántico

`semantic.py` recorre el AST con una pila de ámbitos. Revisa variables declaradas, duplicados dentro de un ámbito, compatibilidad de asignaciones, operandos de operadores y condiciones booleanas. Se acepta asignar `int` a `double`, pero no `double` a `int`. La división produce `double`; el módulo requiere dos `int`.

También comprueba inicialización definida. Una declaración sin valor se puede asignar después, pero no leer antes. Para garantizar inicialización después de un `if/else`, ambas ramas deben asignar; una asignación dentro de `while` no basta porque el ciclo puede ejecutar cero vueltas. El análisis es conservador y no deduce condiciones constantes. Se rechazan los nombres reservados por el proyecto para JavaScript.

El análisis semántico puede reunir varios mensajes con línea y columna. No ejecuta el fuente ni comprueba la terminación de ciclos.

## Tabla de símbolos

Cada `Symbol` registra nombre fuente, tipo, línea de declaración y ámbito (`global`, `bloque 1`, etc.). La búsqueda empieza en el ámbito más interno y continúa hacia afuera. Se permiten nombres iguales en ámbitos diferentes.

La ventana muestra la tabla y `cli.py --symbols` la imprime. Si el análisis semántico falla, se conservan los símbolos encontrados, pero no se genera JS ni código intermedio.

## Código intermedio

`intermediate.py` genera instrucciones con `op`, `arg1`, `arg2` y `result`. Una operación aritmética produce un temporal; `declare`, `print`, `if_false`, `goto` y las etiquetas representan almacenamiento, salida y control de flujo. Los nombres como `a@global` y `a@b1` distinguen variables de ámbitos diferentes.

Por ejemplo, para `int a = 10; int b = 20; System.out.println(a + b);`:

```text
declare int a@global
a@global = 10
declare int b@global
b@global = 20
t1 = a@global + b@global
print t1
```

En `while`, la etiqueta de inicio queda antes de evaluar la condición para repetirla en cada vuelta. `&&` y `||` usan saltos y mantienen el cortocircuito. El listado se ve en la ventana, con `--intermediate` en consola y en `intermedio.txt` al exportar.

## Traducción a JavaScript y exportación

`translator.py` recorre el AST: los tipos fuente se declaran con `let`, la impresión se convierte en `console.log`, y las asignaciones, expresiones y bloques mantienen su estructura. Se añaden paréntesis para preservar el árbol y las cadenas se codifican como JSON.

Las variables locales que ocultan una externa se renombran como `$x_1`. Esto evita que la zona temporal muerta de JavaScript cambie las lecturas previas de la variable externa. El carácter `$` no se admite en identificadores fuente y evita colisiones con esos nombres generados. La tabla de símbolos conserva los nombres originales. La función de traducción a C++ existente se conserva; la aplicación integrada usa JavaScript.

`export_browser()` guarda `programa.js`, `index.html` e `intermedio.txt`. El HTML carga el JS externo y muestra la salida de `console.log` mediante `textContent`, además de mantener la salida de consola. Hay que conservar HTML y JS juntos.

## Integración, errores y pruebas

`Compilation` devuelve tokens, AST, símbolos, instrucciones, JavaScript y lexer utilizado. `CompilationError` incluye la etapa, mensajes y resultados parciales disponibles. `stage_report()` distingue etapas correctas, con error y no ejecutadas. El lexer y el parser detienen el análisis en su primer error; no hay recuperación sintáctica.

La ventana invalida resultados al editar el fuente y bloquea guardar o abrir como válido un análisis fallido. En consola, los códigos de salida son `0` (correcto), `1` (error del lenguaje) y `2` (problema de archivos).

Las 42 pruebas en `tests/` cubren las etapas, inicialización, ámbitos, ejecución de las instrucciones intermedias con un intérprete de pruebas, JS real en Node, scripts HTML con DOM mínimo, consola y widgets Tkinter. `smoke_check.py` comprueba además los recursos y la integración dentro del `.exe` empaquetado. No sustituye una prueba en otro equipo sin Python, que continúa pendiente.

## Archivos de entrega

`Compilador_Integrado.spec` incluye los recursos de Tk/Tcl, los ejemplos y el lexer FLEX disponible. `CREAR_EXE.bat` ejecuta las pruebas, construye y verifica el `.exe`. `requirements-build.txt` contiene la dependencia opcional para reconstruirlo.

`crear_entrega.py` prepara un ZIP bajo 20.000.000 bytes con una lista explícita de archivos, manifiesto SHA-256 e inventario. Su opción `--verificar` extrae y prueba el contenido entregado. Se conservan los fuentes de FLEX, su C generado, el binario y las referencias históricas; se excluyen cachés, entornos virtuales y temporales de compilación.
