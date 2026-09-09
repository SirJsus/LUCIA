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

Las partidas que no empiezan en la posición estándar se marcan con
`CustomPositionBadge`, a partir del campo `starts_from_custom_position` que
trae `GET /games`; el visor hace lo mismo en su cabecera.
