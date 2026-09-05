# ADR-0002 · Stockfish y Lc0 como sub-módulos git compilados localmente

**Estado:** aceptado · **Fecha:** 2026-09-05

## Contexto

Queremos "volcar" Stockfish y Lc0 en el repo. Opciones: (a) copiar el código fuente, (b) sub-módulos git fijados a un tag, (c) descargar binarios pre-compilados.

## Decisión

**(b) Sub-módulos** en `engines/stockfish` y `engines/lc0`, fijados a un tag de release. `scripts/setup-engines.sh` los compila a `engines/bin/` con optimizaciones para la CPU local (`ARCH=x86-64-avx2` o superior). Redes de Lc0 se descargan a `engines/networks/`. Binarios y redes están en `.gitignore`.

## Razones

- Copiar el fuente rompe la trazabilidad con upstream y dificulta actualizar.
- Compilar localmente da el mejor rendimiento (instrucciones de CPU específicas) y no depende de terceros que publiquen binarios.
- Los binarios pre-compilados quedan como *fallback* opcional en el script.

## Consecuencias

- Clonar el repo requiere `git clone --recurse-submodules` o `make engines`.
- Lc0 requiere Meson + Ninja y, para GPU, CUDA/OpenCL. En CPU se compila con backend `blas` o `eigen`.
- Al no modificar el fuente de los motores, cualquier motor UCI externo también funciona (RNF-9).
