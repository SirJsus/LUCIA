# ADR-0004 · Licencia GPL-3.0

**Estado:** aceptado · **Fecha:** 2026-09-05

## Contexto

Stockfish, Lc0 y chessground son GPL-3.0. LUCIA los integra y los distribuye (sub-módulos, scripts de compilación, tablero en el frontend).

## Decisión

Todo el repositorio se publica bajo **GPL-3.0-or-later**.

## Razones

- Comunicarse con un motor por UCI como proceso separado no obliga a GPL por sí solo, pero **distribuir** los motores y **enlazar** chessground en el frontend sí lo hace en la práctica. Adoptar GPL evita cualquier zona gris.
- Coherente con el principio "sin muro de pago, open source".

## Consecuencias

- Cualquier dependencia nueva debe ser compatible con GPL-3.0 (MIT, BSD, Apache-2.0, CC0 lo son).
- Si algún día se quisiera un producto propietario encima, tendría que reescribirse la capa GPL (chessground) y no distribuir motores.
