"""Modelos tipados de las respuestas de la API pública de chess.com.

Los nombres de campo respetan tal cual el JSON de chess.com (excepción de
idioma para claves de APIs de terceros, ver `CLAUDE.md` y el agente
`bautizador`): no se traducen ni se renombran, para poder cruzarlos con la
documentación oficial en https://www.chess.com/news/view/published-data-api
sin ambigüedad.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChessComPlayer(BaseModel):
    """Respuesta de GET /pub/player/{username} (RF-1.1)."""

    model_config = ConfigDict(extra="ignore")

    username: str
    player_id: int
    title: str | None = None
    name: str | None = None
    country: str  # URL tipo https://api.chess.com/pub/country/MX
    joined: int  # epoch seconds
    last_online: int | None = None
    followers: int | None = None
    is_streamer: bool = False
    verified: bool = False


class ChessComRatingBucket(BaseModel):
    """Un bloque de rating dentro de /pub/player/{username}/stats,
    p. ej. `chess_rapid`, `chess_blitz`, `chess_bullet`."""

    model_config = ConfigDict(extra="ignore")

    last: dict | None = None  # {"rating": int, "date": epoch, "rd": int}
    best: dict | None = None
    record: dict | None = None  # {"win": int, "loss": int, "draw": int}


class ChessComPlayerStats(BaseModel):
    """Respuesta de GET /pub/player/{username}/stats (RF-1.6).

    Chess.com añade bloques nuevos con el tiempo (`chess_daily`,
    `chess_rapid`, `chess_blitz`, `chess_bullet`, `tactics`, `puzzle_rush`,
    tableroque `chess960` variantes...). En vez de listar cada uno, se
    conserva el JSON crudo y se exponen los buckets de partida más usados
    como atajo tipado.
    """

    model_config = ConfigDict(extra="allow")

    chess_daily: ChessComRatingBucket | None = None
    chess_rapid: ChessComRatingBucket | None = None
    chess_blitz: ChessComRatingBucket | None = None
    chess_bullet: ChessComRatingBucket | None = None


class ChessComGame(BaseModel):
    """Una partida dentro de GET /pub/player/{username}/games/{YYYY}/{MM}
    (RF-1.2). `pgn` trae los relojes por jugada como comentarios `%clk`
    cuando el control de tiempo los registra; usar `parse_move_clocks` de
    `lucia_chesscom.pgn` para extraerlos.
    """

    model_config = ConfigDict(extra="ignore")

    url: str
    pgn: str
    time_control: str
    end_time: int  # epoch seconds
    rated: bool
    time_class: str  # "bullet" | "blitz" | "rapid" | "daily"
    rules: str  # "chess" | "chess960" | ...
    white: ChessComGamePlayer
    black: ChessComGamePlayer
    eco: str | None = None  # URL a la apertura en chess.com, si la reportó
    fen: str | None = None  # posición final, si la partida no llegó a jaque mate normal
    uuid: str | None = None


class ChessComGamePlayer(BaseModel):
    """Bloque `white`/`black` dentro de una partida: rating y resultado."""

    model_config = ConfigDict(extra="ignore")

    username: str
    rating: int
    result: str  # "win" | "checkmated" | "resigned" | "timeout" | "agreed" | ...


ChessComGame.model_rebuild()
