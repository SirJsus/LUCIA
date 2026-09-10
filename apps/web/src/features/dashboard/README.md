# `features/dashboard`

Estadísticas de la práctica propia (RF-3.1 a RF-3.5): marcador y rating por
control de tiempo, partidas por mes, rendimiento por apertura, pérdida de
ventaja por fase, reparto de errores por tipo y calidad de juego según el reloj
que quedaba. Todo se agrega en la API (`GET /stats/{username}`); aquí solo se
presenta.

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
