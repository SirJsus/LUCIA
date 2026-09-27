# ADR-0023 · En las pantallas de entrenamiento entra la capa de ocupación, no la barra de evaluación, y las marcas arrancan apagadas

**Estado:** aceptado · **Fecha:** 2026-09-22

## Contexto

Las tres pantallas de entrenamiento con tablero —el puzzle de RF-4.1, la línea
del drill de RF-4.2 y la partida de sparring de RF-4.3, que es también la de
re-jugar de RF-4.4— nacieron **sin barra de evaluación**, al contrario que el
visor (RF-5) y el tablero de análisis (RF-6). El motivo se escribió pantalla a
pantalla: en un puzzle la evaluación de la posición es media respuesta, en un
drill delata la línea que hay que recordar, y en sparring una barra diciendo a
cada jugada quién va ganando convierte la partida en un análisis asistido.

RF-7 llegó después con una capa que se enciende **sobre cualquier tablero**:
quién ataca y quién defiende cada casilla, los rayos X, las clavadas y las
piezas colgadas, todo calculado en el cliente a partir del FEN que ya está en
pantalla, sin motor, sin endpoint y sin guardar nada. Entró primero en el visor
y en el tablero de análisis (2026-09-19) y quedó la pregunta obvia: ¿entra
también en entrenamiento, o cae del mismo lado que la barra de evaluación?

La pregunta no es retórica, porque las dos cosas se parecen en pantalla —dos
adornos encima del mismo tablero— y porque una de las marcas, las piezas
colgadas (RF-7.4), **sí** resuelve puzzles tácticos: rodear la dama del rival
que está sin defender es media solución, y durante una partida de sparring es
el aviso de blunder que un rival calibrado no debe dar. Si la respuesta fuera
"lo que ayuda no entra", la capa se quedaría fuera entera.

Las opciones eran cuatro:

1. **Dejar la capa fuera del entrenamiento**, por el mismo criterio que dejó
   fuera la barra. Cuesta contradecir la cabecera de RF-7 —que dice desde el
   primer día que la capa se activa sobre cualquier tablero— y deja al puzzle
   como el único tablero de la aplicación donde no se puede contar cuántos
   atacantes tiene una casilla, que es aritmética de la posición que se está
   mirando, no una opinión.
2. **Meter también la barra**, por coherencia de columna: los cinco tableros
   iguales. Es lo que convierte el ejercicio en un análisis asistido, y anula
   lo que hace útil al puzzle (ADR-0017: el puzzle abierto viaja sin nada que
   lo resuelva; la barra sería exactamente eso, por otra vía).
3. **Meter la capa con las marcas encendidas**, como en el visor. Es la
   coherencia literal —el mismo panel en el mismo sitio con el mismo estado
   inicial— y es la que delata la táctica sin que nadie la haya pedido.
4. **Meter la capa con las marcas apagadas** y decirlo en el propio panel.

## Decisión

**En las pantallas de entrenamiento con tablero entra la capa de ocupación y no
la barra de evaluación. La frontera es de dónde sale el dato: lo que se lee de
la posición que ya está en pantalla entra; lo que es la opinión del motor sobre
esa posición, no. Y las tres marcas de RF-7.4, RF-7.5 y RF-7.6 arrancan
apagadas, porque el conteo es lectura y la conclusión es respuesta.**

- **Qué entra**: el conteo de atacantes y defensores (RF-7.3) y el mapa de
  calor (RF-7.1), encendidos con el atajo `O` como en las otras dos pantallas.
  Es aritmética sobre el FEN visible: quien lo cuenta a mano llega al mismo
  número, solo que más despacio.
- **Qué no entra**: la barra de evaluación (`EvalBar`/`BoardWithEvalBar`), la
  probabilidad de victoria y, mientras el ejercicio está abierto, todo lo que
  el servidor se guarda (ADR-0017 para el puzzle, y la línea entera para el
  drill). Ninguna de las tres pantallas monta `BoardWithEvalBar`: montan
  `features/training/TrainingBoard`, que es la columna de tablero sin barra.
- **Qué arranca apagado**: las piezas colgadas (RF-7.4), los rayos X (RF-7.5) y
  las clavadas (RF-7.6), con `marksOnByDefault: false`. Las tres juntas y no
  solo la que delata: el panel las presenta como tres controles iguales, y
  arrancar con una sí y otra no obligaría a explicar ahí por qué esa.
- **Apagadas, no ausentes**: siguen en el panel, con su ayuda, y el panel dice
  que aquí arrancan apagadas y por qué. Quien las quiere las enciende a
  sabiendas — que es el matiz entre leer la posición y que te la lean.
- **Lo que una marca apagada calla, lo calla también en palabras**: la
  inspección por casilla y lo que esa casilla lee en voz alta omiten "colgada",
  "clavada" y los rayos X cuando su marca está apagada. Si no, apagar la marca
  sería un gesto sin efecto por la vía del teclado.

## Consecuencias

- **La frontera es de origen del dato, no de pantalla.** Ante un adorno nuevo
  sobre un tablero la pregunta es una sola: ¿esto se deduce de la posición que
  se está viendo, o hace falta preguntárselo al motor o al servidor? Lo
  primero puede entrar en entrenamiento; lo segundo, no. No hace falta juzgar
  si una pantalla es "de entrenar" o "de analizar", que es lo que haría falta
  decidir dos veces.
- **Las cinco pantallas con tablero comparten columna pero no estado inicial.**
  Tablero, frase de atajos debajo y panel de ocupación son los mismos en las
  cinco; lo único que cada una elige es `marksOnByDefault`. Que la divergencia
  quepa en un booleano con nombre es lo que la hace revisable: se ve en el
  `useOccupancy` de cada pantalla, sin leer la pantalla entera.
- **El puzzle sigue sin poder resolverse mirando.** La capa cuenta piezas; no
  dice qué jugada gana, ni cuánto vale la posición, ni qué se jugó en la
  partida. Lo que resuelve el ejercicio sigue estando solo en el servidor
  (ADR-0017), así que esta decisión no lo toca.
- **Si algún día se revierte**, el cambio es de una línea por pantalla: quitar
  el `occupancyController` de `TrainingBoard` deja las tres sin capa, y cambiar
  su `marksOnByDefault` las deja como el visor. Revertirlo pediría un ADR nuevo
  que reemplace a este, no editar este.
- **Lo que este ADR no fija**: qué marcas tiene la capa (eso es RF-7), ni si el
  sub-modo se recuerda entre sesiones (RF-7.8, pendiente). Meter la barra de
  evaluación en una pantalla de entrenamiento, o encender ahí las marcas, sí
  sería cambiar esta decisión.

## Ver también

- **RF-7** y **RF-4** en [02-requerimientos.md](../02-requerimientos.md), con
  las notas técnicas del 2026-09-22 donde esto se aplicó requerimiento a
  requerimiento.
- Entrada del **2026-09-22** ("la capa de ocupación en las pantallas de
  entrenamiento") y filas **107** y **108** del inventario de
  [07-coherencia-ui.md](../07-coherencia-ui.md), que son los arreglos concretos
  que salieron de aplicarla.
- [ADR-0017](0017-puzzle-persistido-con-su-solucion-congelada.md): por qué un
  puzzle abierto viaja sin nada que lo resuelva. Esta decisión es el mismo
  criterio llevado a lo que se dibuja encima del tablero.
- [ADR-0022](0022-la-probabilidad-de-victoria-se-cuenta-desde-quien-entrena.md):
  el precedente de forma — una frontera de coherencia de interfaz escrita como
  decisión y acotada para que no se extienda sola.
- `apps/web/src/features/training/TrainingBoard.tsx` (la columna de las tres
  pantallas), `apps/web/src/components/board/useOccupancy.ts`
  (`marksOnByDefault`) y `OccupancyPanel.tsx` (donde se dice en pantalla).
