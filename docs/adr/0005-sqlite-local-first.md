# ADR-0005 · SQLite como base de datos local-first

**Estado:** aceptado · **Fecha:** 2026-09-05

## Contexto

Un solo usuario, ejecución local, decenas de miles de partidas y cientos de miles de jugadas analizadas como máximo.

## Decisión

**SQLite** vía SQLAlchemy 2 async (`aiosqlite`), con migraciones Alembic. Archivo único en `data/lucia.db`.

## Razones

- Cero configuración, un archivo respaldable, consultable con cualquier cliente SQL.
- Volumen de datos muy dentro de lo que SQLite maneja con holgura.
- SQLAlchemy permite migrar a PostgreSQL cambiando la URL si aparece multiusuario.

## Consecuencias

- Escrituras concurrentes limitadas: el worker de análisis escribe por lotes. Activar `journal_mode=WAL`.
- Agregaciones pesadas se hacen en polars sobre extractos, no con SQL complejo.
