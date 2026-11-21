# Ejemplos para la demostración y las pruebas

Las rutas originales se mantienen porque las utilizan la aplicación y las pruebas. Los archivos `.java` contienen el lenguaje simplificado del proyecto, sin clases ni método `main`.

## Programas válidos

| Archivo | Qué demuestra | Resultado |
| --- | --- | --- |
| `demo.java` | Declaraciones, cuatro tipos, impresión, `if/else`, lógica y `while` | Compilación correcta; es el ejemplo cargado por la ventana |
| `valido_completo.java` | Asignación en ambas ramas, precedencia, decimales, Unicode, ámbitos, módulo y lógica | Compilación correcta; prueba más operadores y ámbitos |

Ejecuta desde la raíz del proyecto:

```powershell
py -3 cli.py ejemplos/demo.java --lexer python --symbols --intermediate --out salida_demo
py -3 cli.py ejemplos/valido_completo.java --lexer python --out salida_completa
```

Los dos comandos deben terminar con código `0`. Abre el `index.html` de la carpeta elegida. La salida de `demo.java` es:

```text
Compilador integrado
30
La condición se cumple
0
1
2
```

La salida de `valido_completo.java` es:

```text
Compilación válida
14
2.5
7
0
1
2
4
true
```

## Entradas con errores intencionales

| Archivo | Etapa | Motivo | Ubicación esperada |
| --- | --- | --- | --- |
| `error_lexico.java` | Léxica | Carácter `@` no reconocido | Línea 2, columna 1 |
| `error_sintactico.java` | Sintáctica | Falta `;` después de la primera declaración | Se detecta al comenzar `System` en la línea 2 |
| `error_semantico.java` | Semántica | Se asigna `String` a una variable `int` | Asignación de `edad` en la línea 2 |
| `error_inicializacion.java` | Semántica | Se lee `contador` antes de asignarle un valor | Uso de `contador` en la línea 2 |

```powershell
py -3 cli.py ejemplos/error_lexico.java --lexer python
py -3 cli.py ejemplos/error_sintactico.java --lexer python
py -3 cli.py ejemplos/error_semantico.java --lexer python
py -3 cli.py ejemplos/error_inicializacion.java --lexer python
```

Los cuatro deben terminar con código `1`, indicar la etapa del error y no exportar archivos nuevos. Se pueden repetir con `--lexer flex` después de reconstruir el binario o usando el ZIP de la Release, que sí lo incluye; el texto exacto del error léxico puede variar entre implementaciones.

En la ventana, copia el contenido del archivo al editor y pulsa **Analizar y traducir**. Para los errores, revisa **Estado y errores** y los resultados parciales. Para los válidos, revisa también **Tabla de símbolos**, **AST sintáctico** y **Código intermedio**.

## Suite automática

```powershell
py -3 -m unittest discover -s tests -v
```

Las pruebas incluyen estos ejemplos y otros casos de tipos, bloques, variables no declaradas, duplicados, inicialización, precedencia, cortocircuito, exportación y salida JavaScript.
