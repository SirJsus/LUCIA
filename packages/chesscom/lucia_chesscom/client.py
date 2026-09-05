"""Cliente asíncrono de la API pública de chess.com.

Reglas de la API (RF-1.4 / RNF-10):
- User-Agent identificable obligatorio.
- Peticiones secuenciales; backoff exponencial en 429.
- Los archivos mensuales pasados son inmutables: cachear. Solo el mes actual cambia.

Endpoints previstos:
  GET /pub/player/{username}
  GET /pub/player/{username}/stats
  GET /pub/player/{username}/games/archives
  GET /pub/player/{username}/games/{YYYY}/{MM}
"""

from __future__ import annotations

import httpx

BASE_URL = "https://api.chess.com/pub"


class ChessComClient:
    def __init__(self, user_agent: str, timeout: float = 30.0) -> None:
        self._http = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            http2=True,
        )

    async def get_player(self, username: str) -> dict:
        raise NotImplementedError

    async def get_stats(self, username: str) -> dict:
        raise NotImplementedError

    async def get_archives(self, username: str) -> list[str]:
        raise NotImplementedError

    async def get_month_games(self, username: str, year: int, month: int) -> list[dict]:
        raise NotImplementedError

    async def aclose(self) -> None:
        await self._http.aclose()
