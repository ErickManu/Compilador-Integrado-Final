# Guion breve para demostrar el compilador

Este es nuestro compilador integrado. Recibe un código escrito en un Java simplificado, lo analiza y lo traduce a JavaScript para poder ejecutarlo en el navegador.

Primero está el análisis léxico, que separa el programa en tokens. Podemos consultar la tabla para ver las palabras, variables, números y símbolos identificados. El proyecto incluye FLEX y, una vez compilado, lo podemos seleccionar en esta primera fase.

Después viene el análisis sintáctico, que confirma que la estructura del programa esté bien escrita. Por ejemplo, verifica los puntos y comas y los bloques de instrucciones.

En tercer lugar está el análisis semántico. Aquí se revisa que las variables estén declaradas y que no les asignemos valores de un tipo incorrecto. La tabla de símbolos nos enseña qué variables se encontraron.

La pestaña AST sintáctico muestra la estructura reconocida. Si el programa pasa los análisis, la pestaña Código intermedio muestra instrucciones de tres direcciones: temporales para expresiones, nombres por ámbito y etiquetas con saltos para condiciones y ciclos. Las condiciones lógicas conservan el cortocircuito.

El generador también produce código JavaScript. Guardamos esa traducción como `programa.js` junto a `index.html` e `intermedio.txt`, abrimos el HTML en el navegador y vemos el resultado. También podemos presionar F12 para verlo en la consola.

Por último, cambiamos un ejemplo para provocar un error semántico. Así mostramos que no se traduce ni ejecuta un programa que tenga errores detectados durante el análisis.

Para evidenciar errores de cada etapa, usamos `ejemplos/error_lexico.java`, `error_sintactico.java`, `error_semantico.java` y `error_inicializacion.java`. El panel distingue etapas correctas, la etapa con error y las que no se ejecutaron. Para probar más operadores y ámbitos, usamos `valido_completo.java`.
