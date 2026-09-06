import httpx
import pytest
import respx
from lucia_chesscom import ChessComClient, ChessComNotFoundError

UA = "LUCIA-tests/0.1 (contacto: test@example.com)"


def test_user_agent_generico_falla_rapido() -> None:
    with pytest.raises(ValueError):
        ChessComClient(user_agent="")
    with pytest.raises(ValueError):
        ChessComClient(user_agent="LUCIA/0.1")


@pytest.mark.asyncio
async def test_get_player() -> None:
    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        mock.get("/player/hikaru").mock(
            return_value=httpx.Response(
                200,
                json={
                    "username": "hikaru",
                    "player_id": 15448422,
                    "country": "https://api.chess.com/pub/country/US",
                    "joined": 1389043258,
                },
            )
        )
        async with ChessComClient(user_agent=UA) as client:
            player = await client.get_player("hikaru")
        assert player.username == "hikaru"
        assert player.player_id == 15448422


@pytest.mark.asyncio
async def test_sigue_redirecciones_por_casing_del_username() -> None:
    # chess.com redirige (301) cuando el username no viene en su "casing"
    # canónico; encontrado en una prueba en vivo con "MagnusCarlsen".
    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        mock.get("/player/MagnusCarlsen").mock(
            return_value=httpx.Response(
                301, headers={"Location": "https://api.chess.com/pub/player/magnuscarlsen"}
            )
        )
        mock.get("/player/magnuscarlsen").mock(
            return_value=httpx.Response(
                200,
                json={
                    "username": "magnuscarlsen",
                    "player_id": 2,
                    "country": "https://api.chess.com/pub/country/NO",
                    "joined": 0,
                },
            )
        )
        async with ChessComClient(user_agent=UA) as client:
            player = await client.get_player("MagnusCarlsen")
        assert player.username == "magnuscarlsen"


@pytest.mark.asyncio
async def test_get_archives_parsea_anio_mes() -> None:
    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        mock.get("/player/hikaru/games/archives").mock(
            return_value=httpx.Response(
                200,
                json={
                    "archives": [
                        "https://api.chess.com/pub/player/hikaru/games/2024/01",
                        "https://api.chess.com/pub/player/hikaru/games/2024/02",
                    ]
                },
            )
        )
        async with ChessComClient(user_agent=UA) as client:
            meses = await client.get_archives("hikaru")
        assert meses == [(2024, 1), (2024, 2)]


@pytest.mark.asyncio
async def test_get_month_games_404_devuelve_lista_vacia() -> None:
    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        mock.get("/player/hikaru/games/2019/01").mock(return_value=httpx.Response(404))
        async with ChessComClient(user_agent=UA) as client:
            partidas = await client.get_month_games("hikaru", 2019, 1)
        assert partidas == []


@pytest.mark.asyncio
async def test_get_player_404_lanza_excepcion_propia() -> None:
    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        mock.get("/player/no-existe-usuario").mock(return_value=httpx.Response(404))
        async with ChessComClient(user_agent=UA) as client:
            with pytest.raises(ChessComNotFoundError):
                await client.get_player("no-existe-usuario")


@pytest.mark.asyncio
async def test_reintenta_ante_429_respetando_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    dormidos: list[float] = []

    async def fake_sleep(segundos: float) -> None:
        dormidos.append(segundos)

    monkeypatch.setattr("lucia_chesscom.client.asyncio.sleep", fake_sleep)

    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        ruta = mock.get("/player/hikaru")
        ruta.side_effect = [
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(
                200,
                json={
                    "username": "hikaru",
                    "player_id": 1,
                    "country": "https://api.chess.com/pub/country/US",
                    "joined": 0,
                },
            ),
        ]
        async with ChessComClient(user_agent=UA) as client:
            player = await client.get_player("hikaru")

    assert player.username == "hikaru"
    assert dormidos == [2.0]
