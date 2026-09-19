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

    `ply` se acepta y se propaga porque los modelos `sf*` de `python-chess` sí
    lo usan (la misma ventaja en centipawns vale distinto en la jugada 6 que
    en la 60), pero el modelo `lichess`, que es el que usamos, lo ignora:
    depende solo de los centipawns, acotados a ±1000. De ahí que el cliente
    web pueda replicar la fórmula sin saber en qué jugada está (ADR-0006).
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
    win_percent_loss = max(0.0, win_percent_before - win_percent_after)
    accuracy = _ACCURACY_A * math.exp(_ACCURACY_B * win_percent_loss) + _ACCURACY_C
    return min(100.0, max(0.0, accuracy))


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

    weights = _volatility_weights(move_accuracies, window)
    weighted_mean = _weighted_mean(move_accuracies, weights)
    weighted_harmonic_mean = _weighted_harmonic_mean(move_accuracies, weights)
    return min(100.0, max(0.0, (weighted_mean + weighted_harmonic_mean) / 2))


def _volatility_weights(move_accuracies: list[float], window: int) -> list[float]:
    weights = []
    for i in range(len(move_accuracies)):
        window_values = move_accuracies[max(0, i - window) : i + window + 1]
        weights.append(max(_standard_deviation(window_values), 0.5))  # piso para no pesar 0
    return weights


def _standard_deviation(values: list[float]) -> float:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _weighted_mean(values: list[float], weights: list[float]) -> float:
    return sum(value * weight for value, weight in zip(values, weights, strict=True)) / sum(weights)


def _weighted_harmonic_mean(values: list[float], weights: list[float]) -> float:
    # Precisión 0 rompería la media armónica (división entre cero); en la
    # práctica una precisión de exactamente 0 es un blunder total, así que
    # se acota a un mínimo pequeño en vez de excluir la jugada.
    nonzero_values = [max(value, 0.1) for value in values]
    total_weight = sum(weights)
    weighted_inverse_sum = sum(
        weight / value for value, weight in zip(nonzero_values, weights, strict=True)
    )
    return total_weight / weighted_inverse_sum
