# `features/dashboard`

Estadísticas de la práctica propia (RF-3.1 a RF-3.7): marcador y rating por
control de tiempo, partidas por mes, rendimiento por apertura, pérdida de
ventaja por fase, reparto de errores por tipo, calidad de juego según el reloj
que quedaba, evolución mes a mes y comparación del repertorio con la teoría de
maestros. Todo se agrega en la API (`GET /stats?username=…`, y `GET /repertoire`
para la última); aquí solo se presenta.

Las tablas salen de `components/DataTable` y los gráficos de **Recharts**, que
pinta ejes y tooltip con estilos en línea y por eso necesita la paleta como
valores concretos: se la da `lib/chartTheme.ts`, que sigue el tema claro/oscuro
activo.

## Las secciones que dependen de un análisis

Marcador, rating y partidas por mes salen del historial importado; el resto
—precisión, fases, tipos de error, reloj y la columna "Al salir" de aperturas—
necesita partidas analizadas. Cuando no hay ninguna, esas secciones lo dicen con
un `EmptyState` en vez de enseñar ceros, que se leerían como un rendimiento
pésimo. "Con el reloj en la mano" tiene además su propio vacío: solo cuentan las
partidas de chess.com que traen reloj por jugada.

## Por qué fallas, y con el reloj en la mano (RF-3.4 y RF-3.5)

Los tipos de error (`time`, `tactical`, `endgame`, `positional`) y los tramos de
reloj llegan resueltos de la API, que los pide a `lucia_core.insights`. Aquí no
se decide nada: `lib/insights.ts` pone el nombre en español y, debajo de cada
tabla, **la regla con la que el núcleo decidió** —"posicional" no significa nada
para quien no la conoce, y dejarla en un `title` la esconde de quien no pasa el
ratón (criterio C-6 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md))—. El
mismo archivo lo usa el visor para los momentos críticos, para que un tipo de
error se llame igual en las dos pantallas.

## Cómo evolucionas (RF-3.7)

`TrendsSection` dibuja mes a mes la precisión, el rating y los errores por tipo,
con la serie que la API devuelve en `stats.trends`; el tramo —mes natural— lo
decide el backend, el mismo eje que "Partidas por mes" para que las dos se lean
juntas. Aquí solo hay tres cosas propias de la pantalla:

- **La frase de tendencia** (`formatTrendSentence` en `lib/insights.ts`) dice el
  sentido con palabras y no con el signo: en precisión subir es mejorar y en
  errores es empeorar, y un `+3` a secas no distingue las dos cosas.
- **Los errores van por cada cien jugadas**, como los manda la API: el eje habla
  de cómo se jugó, no de cuánto se jugó.
- **El rating es el del control de tiempo más jugado y la pantalla dice cuál**
  (`trends.rating_time_class`). Sin decirlo, la línea parecería "mi rating" y
  sería la de una sola escala.

Solo salen los meses con partidas analizadas, así que la sección tiene su propio
vacío cuando no hay ninguna.

## El repertorio, la única sección que sale a internet (RF-3.6)

`RepertoireSection.tsx` enseña dónde se sale el jugador de la teoría de
maestros. Se lee de lo que LUCIA **ya** preguntó al Opening Explorer de Lichess;
preguntar por lo que falta es un botón aparte, porque es lo único de la
aplicación que necesita conexión mientras se usa
([ADR-0010](../../../../../docs/adr/0010-repertorio-con-red-y-cacheado.md)). De
ahí las tres cosas que la distinguen del resto del panel:

- **Dice siempre cuánto sabe y cuánto le falta.** Una comparación a medias
  presentada como completa mentiría sobre el repertorio del usuario, así que
  mientras falten posiciones lo avisa con el mismo `WarningBox` que el resto de
  la aplicación (criterios C-3 y C-4 de
  [`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)).
- **Dice qué va a pasar al pulsar.** Las posiciones se preguntan de una en una y
  espaciadas, para no abusar de un servicio gratuito ajeno, así que la primera
  vez hacen falta varias pulsaciones; la API manda cuántas trae cada consulta y
  cuánto espera entre ellas para poder decirlo en segundos en vez de dejar una
  barra sin final.
- **Sus dos vacíos no son el mismo.** "Ninguna de tus partidas se sale de la
  teoría" y "todavía no hay comparación" se leen igual con el mismo título y
  significan cosas opuestas (criterio C-3).

## La tabla de aperturas (RF-3.2)

El nombre y el código ECO vienen de la clasificación propia de la API
(`lucia_core.openings`, deducida de las jugadas), no de lo que reporte
chess.com: por eso hay código ECO —chess.com no lo da— y por eso una partida que
llegó a la Najdorf por otro orden de jugadas aparece con las demás. Las partidas
que no empiezan en la posición estándar no tienen apertura y no salen en esta
tabla. El encabezado "ECO" va como `abbr` porque la columna es estrecha y la
sigla no se entiende sola (criterio C-6).

La columna "Al salir" es la otra mitad de RF-3.2: la probabilidad de victoria
media al terminar la apertura, no una puntuación, y por eso el encabezado lo
aclara.
