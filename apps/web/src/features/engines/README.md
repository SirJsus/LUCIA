# `features/engines`

Configuración de Stockfish y Lc0 (RF-5.4): hilos, hash, MultiPV y esfuerzo por
posición. MultiPV no es solo cuántas líneas se ven en vivo: desde RF-10.1 es
también cuántas alternativas se guardan con cada jugada analizada, así que
subirlo da más que enseñar en el visor y cuesta más base de datos por partida.
La ruta del binario se muestra pero no se edita —aceptarla desde el
navegador sería ejecutar un ejecutable arbitrario—; se cambia en `.env` y se
recarga la API.
