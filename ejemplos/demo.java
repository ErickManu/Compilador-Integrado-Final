int a = 10;
int b = 20;
String nombre = "Compilador integrado";
boolean mostrar = true;
int contador = 0;

System.out.println(nombre);
System.out.println(a + b);
if (mostrar && a < b) {
    System.out.println("La condición se cumple");
} else {
    System.out.println("No se cumple");
}
while (contador < 3) {
    System.out.println(contador);
    contador = contador + 1;
}
