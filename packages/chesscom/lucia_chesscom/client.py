"""Cliente asíncrono de la API pública de chess.com.

Reglas de la API (RF-1.4 / RNF-10):
- `User-Agent` identificable obligatorio: chess.com puede bloquear tráfico
  anónimo o mal identificado. Configúralo con datos de contacto reales
  (ver `.env.example`, variable `CHESSCOM_USER_AGENT`).
- Peticiones secuenciales, no paralelas: cada método hace una sola llamada;
  quien orquesta varias (p. ej. recorrer meses) debe hacerlo con `await` uno
  por uno, no con `asyncio.gather`.
- Reintento con backoff exponencial ante `429 Too Many Requests`, respetando
  la cabecera `Retry-After` si la manda.
- Los archivos mensuales pasados son inmutables: solo el mes en curso cambia
  (ver `lucia_chesscom.sync.months_to_sync` para la sincronización incremental).
"""

from __future__ import annotations

import asyncio

import httpx

from .models import ChessComGame, ChessComPlayer, ChessComPlayerStats

BASE_URL = "https://api.chess.com/pub"

_MAX_RETRIES = 5
_BACKOFF_BASE_SECONDS = 1.0


class ChessComNotFoundError(Exception):
    """El recurso no existe: usuario inexistente, o mes sin partidas."""


class ChessComClient:
    def __init__(self, user_agent: str, timeout: float = 30.0) -> None:
        if not user_agent or user_agent.strip() in {"", "LUCIA/0.1"}:
            # Un User-Agent genérico incumple RNF-10 y arriesga que chess.com
            # bloquee las peticiones. Falla rápido en vez de descubrirlo en
            # producción con un 403.
            raise ValueError(
                "CHESSCOM_USER_AGENT debe identificar el proyecto y un contacto real, "
                "p. ej. 'LUCIA/0.1 (contacto: tu@email.com)'. Ver .env.example."
            )
        self._http = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            http2=True,
            # chess.com devuelve 301 cuando el username no está en el "casing"
            # canónico (p. ej. "MagnusCarlsen" -> "magnuscarlsen"); sin esto,
            # httpx no lo sigue por defecto y `raise_for_status()` revienta.
            follow_redirects=True,
        )

    async def get_player(self, username: str) -> ChessComPlayer:
        data = await self._get_json(f"/player/{username}")
        return ChessComPlayer.model_validate(data)

    async def get_stats(self, username: str) -> ChessComPlayerStats:
        data = await self._get_json(f"/player/{username}/stats")
        return ChessComPlayerStats.model_validate(data)

    async def get_archives(self, username: str) -> list[tuple[int, int]]:
        """Meses disponibles como tuplas `(año, mes)`, a partir de las URLs
        que devuelve `/games/archives` (formato `.../games/{YYYY}/{MM}`)."""
        data = await self._get_json(f"/player/{username}/games/archives")
        months: list[tuple[int, int]] = []
        for url in data.get("archives", []):
            year_str, month_str = url.rstrip("/").rsplit("/", 2)[-2:]
            months.append((int(year_str), int(month_str)))
        return months

    async def get_month_games(self, username: str, year: int, month: int) -> list[ChessComGame]:
        try:
            data = await self._get_json(f"/player/{username}/games/{year}/{month:02d}")
        except ChessComNotFoundError:
            return []
        return [ChessComGame.model_validate(g) for g in data.get("games", [])]

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> ChessComClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def _get_json(self, path: str) -> dict:
        for attempt in range(_MAX_RETRIES):
            response = await self._http.get(path)
            if response.status_code == 404:
                raise ChessComNotFoundError(path)
            if response.status_code == 429:
                await asyncio.sleep(_retry_delay_seconds(response, attempt))
                continue
            response.raise_for_status()
            return response.json()
        response.raise_for_status()  # último intento: propaga el error real
        return response.json()


def _retry_delay_seconds(response: httpx.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return _BACKOFF_BASE_SECONDS * (2**attempt)
