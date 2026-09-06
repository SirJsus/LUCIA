"""Precisión basada en probabilidad de victoria (win%), no en centipawns
crudos (RF-2.3), siguiendo el método público de Lichess.

`python-chess` ya trae el modelo estadístico cp/mate → win% que usa Lichess
(`Score.wdl(model="lichess")`), así que ese paso no se reimplementa aquí. Lo
propio de este módulo es el segundo paso, documentado por Lichess: convertir
la caída de win% causada por una jugada en un número de precisión (0-100).
"""

from __future__ import annotations

import math

import chess.engine

_ACCURACY_A = 103.1668
_ACCURACY_B = -0.04354
_ACCURACY_C = -3.1669


def win_percent(score: chess.engine.Score, ply: int = 30) -> float:
    """Probabilidad de victoria (0-100) para quien tiene esa jugada a favor.

    `ply` afecta al modelo estadístico: en jugadas tempranas, la misma
    ventaja en centipawns se traduce en menos probabilidad de victoria que
    en un final (hay más partida por delante para que se complique).
    """
    return score.wdl(model="lichess", ply=ply).expectation() * 100


def move_accuracy(win_percent_before: float, win_percent_after: float) -> float:
    """Precisión (0-100) de una jugada, a partir de cuánto bajó el win% del
    que la jugó. Fórmula pública de Lichess
    (https://lichess.org/page/accuracy): una caída de 0 puntos da 100 de
    precisión; la curva cae rápido al principio y se aplana después, para
    que un blunder adicional en una posición ya perdida no siga penalizando
    igual de fuerte.
    """
    caida = max(0.0, win_percent_before - win_percent_after)
    precision = _ACCURACY_A * math.exp(_ACCURACY_B * caida) + _ACCURACY_C
    return min(100.0, max(0.0, precision))


def game_accuracy(move_accuracies: list[float], window: int = 2) -> float:
    """Precisión agregada de una partida (o de un color dentro de ella).

    Aproximación documentada del método de Lichess, no una reimplementación
    exacta (su fórmula completa no es pública en ese nivel de detalle): se
    pondera cada jugada por la volatilidad de la partida a su alrededor
    (desviación estándar del win% en una ventana móvil), y el resultado es
    el promedio entre la media aritmética y la media armónica ponderadas.
    La media armónica castiga más los valores bajos (blunders aislados);
    promediarla con la aritmética evita que un solo despiste hunda el número
    entero, pero tampoco lo esconde del todo.
    """
    if not move_accuracies:
        return 100.0
    if len(move_accuracies) == 1:
        return move_accuracies[0]

    pesos = _pesos_por_volatilidad(move_accuracies, window)
    media = _media_ponderada(move_accuracies, pesos)
    media_armonica = _media_armonica_ponderada(move_accuracies, pesos)
    return min(100.0, max(0.0, (media + media_armonica) / 2))


def _pesos_por_volatilidad(valores: list[float], window: int) -> list[float]:
    pesos = []
    for i in range(len(valores)):
        ventana = valores[max(0, i - window) : i + window + 1]
        pesos.append(max(_desviacion_estandar(ventana), 0.5))  # piso para no pesar 0
    return pesos


def _desviacion_estandar(valores: list[float]) -> float:
    media = sum(valores) / len(valores)
    varianza = sum((v - media) ** 2 for v in valores) / len(valores)
    return math.sqrt(varianza)


def _media_ponderada(valores: list[float], pesos: list[float]) -> float:
    return sum(v * p for v, p in zip(valores, pesos, strict=True)) / sum(pesos)


def _media_armonica_ponderada(valores: list[float], pesos: list[float]) -> float:
    # Precisión 0 rompería la media armónica (división entre cero); en la
    # práctica una precisión de exactamente 0 es un blunder total, así que
    # se acota a un mínimo pequeño en vez de excluir la jugada.
    valores_seguros = [max(v, 0.1) for v in valores]
    suma_pesos = sum(pesos)
    suma_inversos = sum(p / v for v, p in zip(valores_seguros, pesos, strict=True))
    return suma_pesos / suma_inversos
