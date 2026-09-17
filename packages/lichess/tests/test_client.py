"""Tests del cliente del Opening Explorer, con la respuesta simulada.

La API de Lichess no se llama de verdad aquí: son tests, y golpear un servicio
gratuito ajeno en cada `pytest` es justo lo que RNF-10 pide no hacer. Lo que se
prueba es lo nuestro: que se lee lo que hace falta de la respuesta, que se
espera entre peticiones y que un 429 se reintenta.
"""

import httpx
import pytest
import respx
from lucia_lichess import (
    LichessExplorerAuthError,
    LichessExplorerClient,
    LichessExplorerError,
)

USER_AGENT = "LUCIA-test (contacto: test@example.com)"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

#: Forma real de `GET /masters`, recortada: el explorador devuelve además
#: `topGames`, `recentGames` y `opening`, que no se modelan a propósito.
MASTERS_RESPONSE = {
    "white": 1200,
    "draws": 900,
    "black": 700,
    "moves": [
        {
            "uci": "e2e4",
            "san": "e4",
            "averageRating": 2400,
            "white": 500,
            "draws": 400,
            "black": 300,
        },
        {
            "uci": "d2d4",
            "san": "d4",
            "averageRating": 2410,
            "white": 400,
            "draws": 350,
            "black": 250,
        },
    ],
    "topGames": [],
    "opening": None,
}


@respx.mock
async def test_reads_what_masters_play_in_a_position() -> None:
    respx.get("https://explorer.lichess.org/masters").mock(
        return_value=httpx.Response(200, json=MASTERS_RESPONSE)
    )

    async with LichessExplorerClient(USER_AGENT, min_interval_seconds=0) as client:
        position = await client.masters(STARTING_FEN)

    assert position.games == 2800
    assert [move.san for move in position.moves] == ["e4", "d4"]
    assert position.moves[0].games == 1200  # 500 + 400 + 300


@respx.mock
async def test_identifies_itself_and_asks_only_for_what_it_uses() -> None:
    route = respx.get("https://explorer.lichess.org/masters").mock(
        return_value=httpx.Response(200, json=MASTERS_RESPONSE)
    )

    async with LichessExplorerClient(USER_AGENT, min_interval_seconds=0) as client:
        await client.masters(STARTING_FEN, moves=5)

    request = route.calls.last.request
    assert request.headers["User-Agent"] == USER_AGENT
    assert request.url.params["fen"] == STARTING_FEN
    assert request.url.params["moves"] == "5"
    # Las partidas de ejemplo no se usan: pedirlas sería tráfico ajeno gastado
    # para nada.
    assert request.url.params["topGames"] == "0"


async def test_a_generic_user_agent_is_rejected_before_asking() -> None:
    """Mismo criterio que el cliente de chess.com: fallar aquí es mejor que
    descubrirlo cuando el servicio empiece a bloquear (RNF-10)."""
    with pytest.raises(ValueError):
        LichessExplorerClient("  ")


@respx.mock
async def test_retries_when_the_explorer_asks_to_slow_down() -> None:
    respx.get("https://explorer.lichess.org/masters").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json=MASTERS_RESPONSE),
        ]
    )

    async with LichessExplorerClient(USER_AGENT, min_interval_seconds=0) as client:
        position = await client.masters(STARTING_FEN)

    assert position.games == 2800


@respx.mock
async def test_a_network_failure_is_its_own_error() -> None:
    """Sin conexión no es un fallo de LUCIA: quien llama decide si sigue sin el
    dato o avisa, y para eso necesita distinguirlo."""
    respx.get("https://explorer.lichess.org/masters").mock(
        side_effect=httpx.ConnectError("sin red")
    )

    async with LichessExplorerClient(USER_AGENT, min_interval_seconds=0) as client:
        with pytest.raises(LichessExplorerError):
            await client.masters(STARTING_FEN)


@respx.mock
async def test_sends_the_token_when_there_is_one() -> None:
    """El explorador dejó de admitir peticiones anónimas: sin token responde
    401 a todo, incluido el ejemplo de su propia documentación."""
    route = respx.get("https://explorer.lichess.org/masters").mock(
        return_value=httpx.Response(200, json=MASTERS_RESPONSE)
    )

    async with LichessExplorerClient(
        USER_AGENT, token="lip_untoken", min_interval_seconds=0
    ) as client:
        await client.masters(STARTING_FEN)

    assert route.calls.last.request.headers["Authorization"] == "Bearer lip_untoken"


@respx.mock
async def test_a_missing_or_invalid_token_is_its_own_error() -> None:
    """Reintentar no arregla un token que falta, así que ni se reintenta: se
    dice qué pasa y cómo se arregla."""
    respx.get("https://explorer.lichess.org/masters").mock(
        return_value=httpx.Response(401, html="<html>401</html>")
    )

    async with LichessExplorerClient(USER_AGENT, min_interval_seconds=0) as client:
        with pytest.raises(LichessExplorerAuthError) as error:
            await client.masters(STARTING_FEN)

    assert "LICHESS_TOKEN" in str(error.value)
