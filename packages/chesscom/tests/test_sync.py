from datetime import date

import pytest
from lucia_chesscom import months_to_sync


def test_primera_sincronizacion_trae_todo() -> None:
    archivos = [(2024, 3), (2024, 1), (2024, 2)]
    assert months_to_sync(archivos, last_synced=None) == [(2024, 1), (2024, 2), (2024, 3)]


def test_solo_trae_meses_posteriores_al_ultimo_sincronizado() -> None:
    archivos = [(2024, 1), (2024, 2), (2024, 3)]
    assert months_to_sync(archivos, last_synced=(2024, 2)) == [(2024, 3)]


def test_repite_el_mes_en_curso_por_si_hay_partidas_nuevas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lucia_chesscom.sync.date", _FakeDate)
    archivos = [(2024, 5), (2024, 6)]
    # last_synced es el mes en curso (junio 2024): debe volver a pedirse.
    assert months_to_sync(archivos, last_synced=(2024, 6)) == [(2024, 6)]


def test_sin_meses_nuevos_devuelve_vacio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lucia_chesscom.sync.date", _FakeDate)
    archivos = [(2024, 5)]
    # last_synced ya no es el mes en curso (junio) y no hay nada posterior.
    assert months_to_sync(archivos, last_synced=(2024, 5)) == []


class _FakeDate(date):
    @classmethod
    def today(cls) -> "_FakeDate":
        return cls(2024, 6, 15)
