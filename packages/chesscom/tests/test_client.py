import httpx
import pytest
import respx
from lucia_chesscom import ChessComClient, ChessComNotFoundError

UA = "LUCIA-tests/0.1 (contacto: test@example.com)"


def test_generic_user_agent_fails_fast() -> None:
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
async def test_follows_redirects_for_username_casing() -> None:
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
async def test_get_archives_parses_year_and_month() -> None:
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
            months = await client.get_archives("hikaru")
        assert months == [(2024, 1), (2024, 2)]


@pytest.mark.asyncio
async def test_get_month_games_404_returns_an_empty_list() -> None:
    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        mock.get("/player/hikaru/games/2019/01").mock(return_value=httpx.Response(404))
        async with ChessComClient(user_agent=UA) as client:
            games = await client.get_month_games("hikaru", 2019, 1)
        assert games == []


@pytest.mark.asyncio
async def test_get_player_404_raises_its_own_exception() -> None:
    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        mock.get("/player/no-existe-usuario").mock(return_value=httpx.Response(404))
        async with ChessComClient(user_agent=UA) as client:
            with pytest.raises(ChessComNotFoundError):
                await client.get_player("no-existe-usuario")


@pytest.mark.asyncio
async def test_retries_on_429_respecting_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    slept_seconds: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept_seconds.append(seconds)

    monkeypatch.setattr("lucia_chesscom.client.asyncio.sleep", fake_sleep)

    with respx.mock(base_url="https://api.chess.com/pub") as mock:
        route = mock.get("/player/hikaru")
        route.side_effect = [
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
    assert slept_seconds == [2.0]
