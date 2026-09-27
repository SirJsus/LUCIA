"""Cliente asíncrono del Opening Explorer de Lichess.

Es la **única** parte de LUCIA que necesita red mientras se usa la aplicación
—todo lo demás funciona con lo importado (RNF-1)—, así que se comporta como
invitado en casa ajena, con las mismas reglas que el cliente de chess.com
(RNF-10):

- **Token de Lichess obligatorio.** El explorador dejó de admitir peticiones
  anónimas: responde `401` a todo, incluido el ejemplo de su propia
  documentación, y su especificación declara `security: OAuth2`. El token es
  gratuito y no necesita permisos especiales; se saca en
  <https://lichess.org/account/oauth/token> y se configura en `LICHESS_TOKEN`.
- `User-Agent` identificable, con contacto real.
- Peticiones **secuenciales y espaciadas**: la base de maestros es un servicio
  gratuito y aquí se le pregunta por muchas posiciones seguidas. Entre una y
  otra se espera `min_interval_seconds`.
- Reintento con backoff exponencial ante `429 Too Many Requests`, respetando
  `Retry-After` si viene.

Quien orqueste varias posiciones no debe paralelizarlas: el espaciado lo
garantiza este cliente, y `asyncio.gather` lo saltaría.
"""

from __future__ import annotations

import asyncio
import time

import httpx

from .models import ExplorerPosition

#: El host del explorador es `explorer.lichess.org`, no `lichess.org`: lo dice
#: su propia especificación de API. El antiguo `explorer.lichess.ovh` resuelve
#: a la misma máquina, pero este es el nombre canónico y el del certificado.
BASE_URL = "https://explorer.lichess.org"

_MAX_RETRIES = 5
_BACKOFF_BASE_SECONDS = 1.0

#: Cuántas jugadas distintas se piden por posición. Doce cubre de sobra el
#: repertorio real de una posición de apertura; lo que quede fuera son rarezas
#: que no son "la línea principal" contra la que se compara (RF-3.6).
DEFAULT_MOVES_PER_POSITION = 12


class LichessExplorerError(Exception):
    """El explorador no pudo responder. Se distingue de un fallo de LUCIA
    porque quien llama decide si seguir sin ese dato."""


class LichessExplorerAuthError(LichessExplorerError):
    """Falta el token, o el que hay no vale.

    Es su propio error porque tiene arreglo y quien lo sufre puede aplicarlo:
    los demás fallos del explorador son "vuelve más tarde", este es "saca un
    token y ponlo en `LICHESS_TOKEN`".
    """


class LichessExplorerClient:
    """Consulta la base de partidas de maestros posición a posición."""

    def __init__(
        self,
        user_agent: str,
        token: str = "",
        timeout: float = 20.0,
        min_interval_seconds: float = 1.0,
    ) -> None:
        if not user_agent or not user_agent.strip():
            raise ValueError(
                "El User-Agent debe identificar el proyecto y un contacto real, "
                "p. ej. 'LUCIA/0.1 (contacto: tu@email.com)'. Ver .env.example."
            )
        self._min_interval_seconds = min_interval_seconds
        self._last_request_at = 0.0
        headers = {"User-Agent": user_agent}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._http = httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=timeout)

    async def masters(self, fen: str, moves: int = DEFAULT_MOVES_PER_POSITION) -> ExplorerPosition:
        """Qué juegan los maestros en esa posición.

        Se usa la base de maestros y no la de partidas de Lichess porque la
        pregunta de RF-3.6 es "dónde me salgo de la teoría", y la teoría es lo
        que juega quien sabe, no lo que juega todo el mundo.
        """
        await self._wait_its_turn()
        data = await self._get_json("/masters", params={"fen": fen, "moves": moves, "topGames": 0})
        return ExplorerPosition.model_validate(data)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> LichessExplorerClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def _wait_its_turn(self) -> None:
        """Espacia las peticiones sin depender de que quien llame se acuerde."""
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval_seconds:
            await asyncio.sleep(self._min_interval_seconds - elapsed)
        self._last_request_at = time.monotonic()

    async def _get_json(self, path: str, params: dict) -> dict:
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._http.get(path, params=params)
            except httpx.HTTPError as error:  # sin red, DNS caído, timeout…
                raise LichessExplorerError(str(error)) from error
            if response.status_code == 429:
                await asyncio.sleep(_retry_delay_seconds(response, attempt))
                continue
            if response.status_code in (401, 403):
                # Reintentar no arregla un token que falta o no vale.
                raise LichessExplorerAuthError(
                    "el explorador de Lichess rechazó la petición: hace falta un token. "
                    "Sácalo gratis en https://lichess.org/account/oauth/token (sin permisos "
                    "especiales) y ponlo en LICHESS_TOKEN."
                )
            if response.is_error:
                raise LichessExplorerError(f"{response.status_code} en {path}")
            return response.json()
        raise LichessExplorerError("el explorador sigue limitando las peticiones")


def _retry_delay_seconds(response: httpx.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return _BACKOFF_BASE_SECONDS * (2**attempt)
