// Precedencia, Unicode, tipos, ámbitos, asignación y control de flujo.
int x;
boolean elegir = false;
if (elegir) {
    x = 99;
} else {
    x = 2 + 3 * 4;
}
double mitad = 5 / 2;
String mensaje = "Compilación válida";
System.out.println(mensaje);
System.out.println(x);
System.out.println(mitad);
if (true) {
    int x = 7;
    System.out.println(x);
}
int contador = 0;
while (contador < 3) {
    System.out.println(contador);
    contador = contador + 1;
}
System.out.println(x % 5);
System.out.println(!elegir && x >= 14 || false);
