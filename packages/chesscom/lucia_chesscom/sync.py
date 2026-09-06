"""Sincronización incremental (RF-1.3): qué meses hace falta descargar.

Los archivos mensuales pasados son inmutables una vez que el mes terminó
(chess.com no reescribe partidas viejas); solo el mes en curso puede recibir
partidas nuevas. Esta función es pura y no toca red ni base de datos: recibe
lo que ya se tiene guardado y decide qué falta, para que la API la use junto
con la tabla `sync_state` (ver docs/03-arquitectura.md).
"""

from __future__ import annotations

from datetime import date


def months_to_sync(
    available_archives: list[tuple[int, int]],
    last_synced: tuple[int, int] | None,
) -> list[tuple[int, int]]:
    """Decide qué meses (año, mes) descargar de nuevo.

    - `available_archives`: todos los meses que chess.com reporta para el
      jugador (salida de `ChessComClient.get_archives`, ya parseada a
      tuplas), en cualquier orden.
    - `last_synced`: el último mes que ya se guardó en la base de datos, o
      `None` si nunca se sincronizó (primera importación completa).

    Regla: todo lo posterior a `last_synced` es nuevo por definición. El
    propio `last_synced` se vuelve a descargar solo si es el mes en curso,
    porque ese es el único que puede haber ganado partidas desde la última
    sincronización.
    """
    if last_synced is None:
        return sorted(available_archives)

    current = _current_year_month()
    pending = [ym for ym in available_archives if ym > last_synced]
    if last_synced == current:
        pending.append(last_synced)
    return sorted(set(pending))


def _current_year_month() -> tuple[int, int]:
    today = date.today()
    return (today.year, today.month)
