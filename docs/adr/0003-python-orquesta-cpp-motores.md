# ADR-0003 · Python orquesta, C++ solo en los motores

**Estado:** aceptado · **Fecha:** 2026-09-05

## Contexto

Se planteó escribir la lógica en Python o "irse a lo más puro" en C++.

## Decisión

La lógica (análisis, clasificación, estadísticas, API) se escribe en **Python**. C++ queda exclusivamente dentro de los motores, con los que hablamos por **UCI** vía `python-chess`. Solo se escribirán extensiones C++ (pybind11) si un *profiler* demuestra un cuello de botella real en Python.

## Razones

- Más del 99 % del tiempo de CPU de un análisis está dentro de Stockfish/Lc0, no en el orquestador.
- `python-chess` ya resuelve PGN, FEN, generación de jugadas y el protocolo UCI de forma async y probada.
- Iterar sobre umbrales de clasificación, fórmulas de precisión y extractores de patrones es mucho más rápido en Python.
- El ecosistema de datos (polars, estadística) está en Python.

## Consecuencias

- Requiere un pool de procesos de motor para paralelizar análisis en lote.
- Si en el futuro se necesitan búsquedas propias (por ejemplo, detectar tácticas con árboles personalizados) se evalúa C++ o Rust con bindings, puntualmente.
