# Evidencias de verificación

- `verificacion-compilacion.txt`: registro de la última construcción del ejecutable durante la revisión del 20/11/2026. Incluye las 42 pruebas aprobadas, la construcción con PyInstaller y el resultado de la autoprueba del `.exe`.
- `smoke-exe.json`: resultado de esa autoprueba (`ok: true`, `frozen: true`), con análisis Python/FLEX, exportación y widgets Tkinter desde los recursos empaquetados.

Son copias de los registros originales de `build/`, con las rutas locales sustituidas por marcadores para su publicación. El registro original se conserva localmente; los resultados de pruebas y compilación no se alteraron. `build/` se excluye del ZIP por contener archivos temporales y copias grandes de la compilación.

La preparación del ZIP genera una comprobación adicional después de extraer el contenido entregado. Sus resultados quedan **junto al ZIP**, en `entrega/VERIFICACION_ENTREGA.json` y `entrega/pruebas-paquete.txt`; no se incrustan en el propio ZIP para evitar que la verificación cambie el archivo que acaba de comprobar. `entrega/CONTENIDO_ZIP.txt` enumera todos los miembros y sus tamaños, y registra el SHA-256 del ZIP final.

La auditoría describe los límites de las comprobaciones. Continúa pendiente probar el ejecutable en un segundo Windows sin Python instalado.
