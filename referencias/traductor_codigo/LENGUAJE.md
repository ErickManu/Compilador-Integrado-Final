# Lenguaje fuente: Java simplificado

## 1. Descripción

Este lenguaje es un **subconjunto académico de Java**, no una implementación
completa del lenguaje Java. Un programa es una secuencia de instrucciones; no se
escriben `public class`, `public static void main` ni importaciones. Distingue
mayúsculas y minúsculas. Los espacios, tabulaciones y saltos de línea separan
tokens, pero no sustituyen el punto y coma.

## 2. Tipos de datos

| Fuente | Uso previsto | JavaScript | C++ |
| --- | --- | --- | --- |
| `int` | Enteros | `let` | `int` |
| `double` | Decimales | `let` | `double` |
| `String` | Cadenas | `let` | `string` |
| `boolean` | Lógicos | `let` | `bool` |

Los tipos se conservan en el AST. No se comprueba la compatibilidad entre tipos.

## 3. Variables

```java
int edad = 20;
double promedio = 85.5;
String nombre = "Erick";
boolean activo = true;
int contador;
```

Una declaración contiene un tipo, un identificador, una inicialización opcional
y `;`. Solo se admite una variable por declaración. Los identificadores siguen
`[A-Za-z_][A-Za-z0-9_]*`. No se admiten tildes, `$` ni palabras reservadas del
subconjunto como nombres de variables. `System`, `out` y `println` también se
reservan. Evita además palabras reservadas del lenguaje destino y los nombres
`console`, `cout`, `endl`, `std`, `main` y `string`.

No se insertan inicializadores por defecto. Asigna un valor antes de leer una
variable declarada sin inicialización.

## 4. Asignaciones

```java
contador = 0;
contador = contador + 1;
edad = 25;
```

El lado izquierdo es un identificador y el derecho una expresión. No se soportan
`+=`, `++`, asignaciones encadenadas ni asignaciones dentro de expresiones.

## 5. Valores

- Enteros: `0`, `20`, `125`.
- Decimales: `0.5`, `85.5`, `10.0` (dígitos a ambos lados del punto).
- Cadenas entre comillas dobles: `"Hola mundo"`, `"Erick"`, `""`.
- Booleanos: `true`, `false`.

El signo es un operador unario: `-20`, `+3`, `-(2 + 1)`.
Los ceros iniciales se normalizan como números decimales: `007` se genera como `7`.
No se admite notación científica, hexadecimal, sufijos, `null` ni caracteres
entre comillas simples. Se admiten caracteres Unicode dentro de cadenas.

Escapes permitidos en cadenas: `\"` (comilla), `\\` (barra inversa), `\n`
(salto de línea), `\r` (retorno), `\t` (tabulación), `\b` (retroceso) y `\f`
(salto de página). No se permiten saltos de línea literales dentro de una cadena
ni escapes `\uXXXX`. Las cadenas se decodifican y vuelven a codificar al generar.

## 6. Operadores aritméticos

`+`, `-`, `*`, `/`, `%`. Se admite `+` y `-` unarios.

```java
int resultado = 10 + 5 * 2;
int agrupado = (10 + 5) * 2;
int resto = resultado % 3;
```

La multiplicación, división y módulo tienen prioridad sobre suma y resta.
Operadores binarios de igual prioridad se agrupan de izquierda a derecha:
`10 - 3 - 2` representa `(10 - 3) - 2`.

## 7. Operadores relacionales

`>`, `<`, `>=`, `<=`, `==`, `!=`.

```java
boolean mayor = edad >= 18;
boolean diferente = edad != 20;
```

Se usan principalmente sobre números. La semántica de igualdad de referencias
Java para cadenas no se implementa.

## 8. Operadores lógicos

`&&` (y), `||` (o), `!` (negación).

```java
boolean permitido = edad >= 18 && activo;
boolean aviso = !activo || edad < 18;
```

Precedencia de mayor a menor:

| Prioridad | Operadores |
| --- | --- |
| 1 | Paréntesis y valores |
| 2 | `!`, `-`, `+` unarios |
| 3 | `*`, `/`, `%` |
| 4 | `+`, `-` binarios |
| 5 | `<`, `>`, `<=`, `>=` |
| 6 | `==`, `!=` |
| 7 | `&&` |
| 8 | `||` |

Los unarios se agrupan de derecha a izquierda. Los paréntesis pueden cambiar la
agrupación en cualquier expresión.

## 9. System.out.println

```java
System.out.println(nombre);
System.out.println("Hola mundo");
System.out.println(edad + 1);
```

Acepta exactamente una expresión y termina con `;`. No se admiten llamadas
vacías, varios argumentos ni `System.out.print`.

## 10. if

```java
if (edad >= 18) {
    System.out.println("Mayor de edad");
}
```

La condición necesita paréntesis y el cuerpo necesita llaves, incluso si contiene
una sola instrucción. Los bloques pueden estar vacíos o contener otros bloques
`if` y `while`.

## 11. if/else

```java
if (edad >= 18) {
    System.out.println("Mayor");
} else {
    System.out.println("Menor");
}
```

`else` es opcional. Para encadenar condiciones, usa otro `if` dentro del bloque
de `else`; la forma abreviada `else if` no pertenece a este subconjunto.

## 12. while

```java
int contador = 0;
while (contador < 3) {
    System.out.println(contador);
    contador = contador + 1;
}
```

La condición necesita paréntesis y el cuerpo necesita llaves. La interfaz traduce
el ciclo sin ejecutarlo.

## 13. Gramática simplificada

EBNF: `{ ... }` indica repetición, `[ ... ]` opcionalidad y las comillas señalan
terminales. Las llaves terminales se escriben entre comillas.

```ebnf
programa     = { instruccion }, EOF ;
instruccion  = declaracion | asignacion | impresion | condicional | ciclo ;
tipo         = "int" | "double" | "String" | "boolean" ;
declaracion  = tipo, IDENTIFIER, [ "=", expresion ], ";" ;
asignacion   = IDENTIFIER, "=", expresion, ";" ;
impresion    = "System", ".", "out", ".", "println", "(", expresion, ")", ";" ;
condicional  = "if", "(", expresion, ")", bloque, [ "else", bloque ] ;
ciclo        = "while", "(", expresion, ")", bloque ;
bloque       = "{", { instruccion }, "}" ;
expresion    = disyuncion ;
disyuncion   = conjuncion, { "||", conjuncion } ;
conjuncion   = igualdad, { "&&", igualdad } ;
igualdad     = relacion, { ( "==" | "!=" ), relacion } ;
relacion     = suma, { ( ">" | "<" | ">=" | "<=" ), suma } ;
suma         = producto, { ( "+" | "-" ), producto } ;
producto     = unaria, { ( "*" | "/" | "%" ), unaria } ;
unaria       = ( "!" | "-" | "+" ), unaria | primaria ;
primaria     = NUMBER | STRING_LITERAL | "true" | "false" | IDENTIFIER
             | "(", expresion, ")" ;
```

El lexer emite `INT`, `DOUBLE`, `STRING_TYPE`, `BOOLEAN_TYPE`, `IDENTIFIER`,
`NUMBER`, `STRING_LITERAL`, `TRUE`, `FALSE`, `IF`, `ELSE`, `WHILE`, `SYSTEM`,
`OUT`, `PRINTLN`, `PLUS`, `MINUS`, `MULTIPLY`, `DIVIDE`, `MODULO`, `ASSIGN`,
`EQUAL`, `NOT_EQUAL`, `GREATER`, `LESS`, `GREATER_EQUAL`, `LESS_EQUAL`, `AND`,
`OR`, `NOT`, `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `SEMICOLON`, `DOT` y `EOF`.
Cada token guarda `type`, `value`, `line` y `column`, con posiciones desde 1.

## 14. Traducción Java → JavaScript

Los cuatro tipos declarados se generan como `let`. Las asignaciones conservan su
estructura y `System.out.println(expresion);` se genera como
`console.log(expresion);`. Los operadores se conservan, incluidos `==` y `!=`.
No se sustituyen por `===` o `!==`.

`if`, `else`, `while` y sus bloques se recorren de forma recursiva. Cada nivel de
bloque añade cuatro espacios. No se añade una función envolvente.

## 15. Traducción Java → C++

Se usa la tabla de tipos de la sección 2 y `cout << expresion << endl;` para
imprimir. Se incluye siempre `<iostream>` y se incluye `<string>` si hay una
declaración `String` o un literal de cadena, incluso en bloques anidados.

La salida lleva `using namespace std;` y todas las instrucciones se envuelven en
`int main() { ... }`, que termina con `return 0;`.
Los operadores y bloques se conservan. Las expresiones binarias y unarias se
rodean de paréntesis para preservar el árbol, también al insertarlas en `cout`.

## 16. Ejemplos

Fuente:

```java
int resultado = (10 + 5) * 2;
System.out.println(resultado);
```

JavaScript:

```javascript
let resultado = ((10 + 5) * 2);
console.log(resultado);
```

C++:

```cpp
#include <iostream>
using namespace std;

int main() {
    int resultado = ((10 + 5) * 2);
    cout << resultado << endl;

    return 0;
}
```

El ejemplo completo de la interfaz incluye los cuatro tipos, un `if/else` con
`&&` y un `while`. `PRUEBAS.md` contiene otros cinco casos para cada destino.

## 17. Limitaciones

- No hay clases, métodos, funciones, arreglos, comentarios, `for`, `do`, `switch`,
  `break`, `continue`, `return` de usuario, entrada de datos ni bibliotecas Java.
- No hay análisis semántico, tabla de símbolos ni comprobación de tipos,
  ámbitos, inicialización, rangos, divisiones por cero o terminación de ciclos.
  Un programa sintácticamente aceptado puede ser inválido en el destino.
- Las palabras reservadas del destino y los nombres de su biblioteca no se
  renombran ni se validan. El autor del programa debe evitarlos.
- La suma se ofrece para operaciones numéricas. No se implementa la conversión
  automática de tipos de la concatenación de Java. En particular, sumar dos
  literales de cadena o una cadena y un número puede generar C++ inválido.
- JavaScript usa su tipo `number`: `5 / 2` produce `2.5`; con enteros C++ produce
  `2`. No se reproducen los límites de 32 bits ni los desbordamientos de Java.
  Para resultados comparables, evita divisiones enteras no exactas y usa números
  pequeños. `%` sobre decimales no es válido en C++.
- `cout` imprime booleanos como `1`/`0`; Java y `console.log` usan `true`/`false`.
  La precisión y representación de números decimales también pueden diferir.
- Variables sin inicializar tienen comportamientos distintos según el destino.
  Decláralas y asígnales un valor antes de usarlas.
- El archivo fuente se trata como texto Unicode. Al compilar C++ por separado,
  usa una herramienta y una terminal configuradas para UTF-8.
- La interfaz muestra el primer error encontrado; no intenta recuperar el parser
  para continuar después de un error. Una anidación excesiva se informa como error.
- El programa vacío es válido para el parser; la interfaz solicita contenido
  antes de traducir. La interfaz genera texto y no ejecuta ni compila ese texto.
