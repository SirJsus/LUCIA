"""Lo que devuelve el Opening Explorer de Lichess para una posición.

Solo se modela lo que LUCIA usa —cuántas partidas de maestros hay en esa
posición y qué se juega en ella—, no la respuesta entera: `topGames`,
`recentGames` y los ratings por tramo se ignoran a propósito. Cuanto menos se
modele de una API ajena, menos se rompe cuando cambie.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExplorerMove(BaseModel):
    """Una jugada jugada en esta posición, con el resultado que dio."""

    model_config = ConfigDict(extra="ignore")

    uci: str
    san: str
    white: int
    """Partidas que ganaron las blancas tras esta jugada."""
    draws: int
    black: int

    @property
    def games(self) -> int:
        """En cuántas partidas de la base se ha jugado."""
        return self.white + self.draws + self.black


class ExplorerPosition(BaseModel):
    """La posición tal como la ve la base de maestros: cuántas partidas la han
    alcanzado y qué se juega desde ella, de más a menos frecuente."""

    model_config = ConfigDict(extra="ignore")

    white: int
    draws: int
    black: int
    moves: list[ExplorerMove] = Field(default_factory=list)

    @property
    def games(self) -> int:
        return self.white + self.draws + self.black
