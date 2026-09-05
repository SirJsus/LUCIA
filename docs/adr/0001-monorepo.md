# ADR-0001 · Monorepo

**Estado:** aceptado · **Fecha:** 2026-09-05

## Contexto

El proyecto tiene motores C++ (terceros), lógica Python, API y frontend TypeScript. Evolucionan juntos y los contratos entre ellos cambian a menudo al inicio.

## Decisión

Un solo repositorio con `apps/`, `packages/`, `engines/`, `infra/`, `docs/`. Workspaces por lenguaje: **uv** para Python y **pnpm** para TypeScript. Un `Makefile` raíz unifica comandos.

## Consecuencias

- Un PR puede tocar API + tipos + web de forma atómica.
- Los tipos TS se generan desde el OpenAPI de la API dentro del mismo repo.
- Los motores entran como sub-módulos, no como código copiado (ver ADR-0002).
