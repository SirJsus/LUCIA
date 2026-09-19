#!/usr/bin/env python3
"""Genera la tabla de aperturas que usa `lucia_core.openings`.

Fuente: chess-openings de Lichess (https://github.com/lichess-org/chess-openings),
**CC0 1.0 (dominio público)**, compatible con la GPL-3.0 del repositorio
(RNF-5). Son cinco TSV, uno por volumen ECO, con `eco`, `name` y el `pgn` de la
línea.

Lo que se versiona no es ese TSV, sino el resultado de recorrerlo: la posición
a la que lleva cada línea, en EPD. Así `lucia_core.openings` no tiene que
reproducir 3.800 partidas cada vez que arranca —eran un par de segundos— y la
búsqueda es un diccionario por posición, que además reconoce transposiciones:
llegar a la Siciliana por otro orden de jugadas es la misma posición y sale con
el mismo nombre.

El archivo generado se versiona a propósito (RNF-1, local-first): la aplicación
no puede depender de tener red para nombrar una apertura. Este script solo hace
falta para actualizar la tabla cuando Lichess publique cambios:

    uv run python3 scripts/build-openings-table.py

Con `--from-dir DIR` los TSV se leen de un directorio en vez de descargarlos,
para regenerar la tabla sin red o desde una copia concreta:

    uv run python3 scripts/build-openings-table.py --from-dir /tmp/chess-openings
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
from pathlib import Path

import chess.pgn

SOURCE_URL = "https://raw.githubusercontent.com/lichess-org/chess-openings/master/{volume}.tsv"
ECO_VOLUMES = ("a", "b", "c", "d", "e")
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "packages/core/lucia_core/openings/data/openings.tsv"
)


def epd_of(pgn_moves: str) -> str | None:
    """La posición a la que lleva una línea, sin contadores de jugada.

    El EPD es la parte del FEN que identifica una posición —piezas, turno,
    enroques y captura al paso—; los contadores sobran, porque la misma
    posición alcanzada por otro orden de jugadas tiene que dar la misma clave.
    """
    game = chess.pgn.read_game(io.StringIO(pgn_moves))
    return game.end().board().epd() if game is not None else None


def read_volume(volume: str, from_dir: Path | None) -> str:
    """El TSV de un volumen ECO, descargado o leído de una copia local."""
    if from_dir is not None:
        return (from_dir / f"{volume}.tsv").read_text(encoding="utf-8")
    url = SOURCE_URL.format(volume=volume)
    print(f"descargando {url}", file=sys.stderr)
    with urllib.request.urlopen(url) as response:  # noqa: S310 — URL fija y https
        return response.read().decode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-dir",
        type=Path,
        default=None,
        help="directorio con a.tsv … e.tsv ya descargados, en vez de bajarlos",
    )
    from_dir = parser.parse_args().from_dir

    openings: dict[str, tuple[str, str]] = {}
    transpositions = 0

    for volume in ECO_VOLUMES:
        rows = csv.DictReader(io.StringIO(read_volume(volume, from_dir)), delimiter="\t")
        for row in rows:
            epd = epd_of(row["pgn"])
            if epd is None:
                continue
            if epd in openings:
                # Dos líneas distintas que acaban en la misma posición: se
                # queda la primera, que en el orden de Lichess es la de nombre
                # más corto y por tanto la más general.
                transpositions += 1
                continue
            openings[epd] = (row["eco"], row["name"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as output:
        output.write("# Aperturas ECO, generado por scripts/build-openings-table.py\n")
        output.write("# Fuente: lichess-org/chess-openings (CC0 1.0, dominio público)\n")
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(("epd", "eco", "name"))
        for epd, (eco, name) in sorted(openings.items(), key=lambda item: item[1]):
            writer.writerow((epd, eco, name))

    print(
        f"{len(openings)} posiciones escritas en {OUTPUT_PATH} "
        f"({transpositions} transposiciones descartadas)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
