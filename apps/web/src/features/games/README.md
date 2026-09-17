# `features/games`

Lista de partidas importadas con filtros y paginación (RF-5.3) y disparo de la
sincronización con chess.com (RF-1). Desde aquí se entra al visor
([`features/viewer`](../viewer/README.md)).

La tabla sale de `components/DataTable`, y se entra a una partida por el enlace
"Ver partida" del final de la fila: es la misma forma que el listado de
tableros ([`features/board`](../board/README.md)), y el motivo de que sea un
enlace con aspecto de botón y no una fila pulsable es que así se puede abrir en
otra pestaña y se ve dónde hay que pulsar (criterio C-2 de
[`docs/07-coherencia-ui.md`](../../../../../docs/07-coherencia-ui.md)).

Los nueve filtros salen de `components/FilterBar` —los mismos campos que
Estadísticas— y viajan tal cual a `GET /games`. Tres de ellos, **color,
resultado y rival, necesitan un jugador**: la misma partida es victoria para uno
y derrota para el otro, así que sin `username` el servidor los ignora y la
pantalla los enseña deshabilitados con el motivo escrito en la barra (no en un
`title`, que con teclado no aparece). La apertura busca por parte del nombre y
las dos fechas incluyen el día que se indica; los campos de texto esperan a que
se deje de teclear antes de consultar. El porqué de cada decisión está en la
nota de RF-5.3 de
[`docs/02-requerimientos.md`](../../../../../docs/02-requerimientos.md).

La paginación dice "Página N · 25 de 324 partidas": el total sale de la cabecera
`X-Total-Count` de `GET /games`, y sin él no se sabría si el filtro dejó fuera
media colección.

Las partidas que no empiezan en la posición estándar se marcan con
`CustomPositionBadge`, a partir del campo `starts_from_custom_position` que
trae `GET /games`; el visor hace lo mismo en su cabecera.
