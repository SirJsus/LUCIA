from datetime import date

import pytest
from lucia_chesscom import months_to_sync


def test_first_sync_fetches_everything() -> None:
    available_archives = [(2024, 3), (2024, 1), (2024, 2)]
    assert months_to_sync(available_archives, last_synced=None) == [(2024, 1), (2024, 2), (2024, 3)]


def test_only_fetches_months_after_the_last_synced_one() -> None:
    available_archives = [(2024, 1), (2024, 2), (2024, 3)]
    assert months_to_sync(available_archives, last_synced=(2024, 2)) == [(2024, 3)]


def test_repeats_the_current_month_in_case_of_new_games(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lucia_chesscom.sync.date", _FakeDate)
    available_archives = [(2024, 5), (2024, 6)]
    # last_synced es el mes en curso (junio 2024): debe volver a pedirse.
    assert months_to_sync(available_archives, last_synced=(2024, 6)) == [(2024, 6)]


def test_no_new_months_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lucia_chesscom.sync.date", _FakeDate)
    available_archives = [(2024, 5)]
    # last_synced ya no es el mes en curso (junio) y no hay nada posterior.
    assert months_to_sync(available_archives, last_synced=(2024, 5)) == []


class _FakeDate(date):
    @classmethod
    def today(cls) -> "_FakeDate":
        return cls(2024, 6, 15)
