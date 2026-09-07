# LUCIA — guía para agentes

- Monorepo: Python (uv workspace: `apps/api`, `packages/core`, `packages/chesscom`) + TypeScript (pnpm: `apps/web`, `packages/shared-types`). Motores C++ en `engines/` como sub-módulos, no se modifican.
- Lee `docs/02-requerimientos.md` (IDs RF-x / RNF-x) antes de implementar una feature y referencia el ID en el commit.
- Decisiones de arquitectura en `docs/adr/`. Si cambias una, escribe un ADR nuevo, no edites el anterior.
- Idioma: docs y comentarios en español; **identificadores de código en inglés**
  (variables, funciones, clases, módulos, archivos, endpoints, tablas/columnas de
  BD), siguiendo el vocabulario técnico habitual de desarrollo. Claridad y
  explicitud sobre origen/destino de los datos siguen siendo obligatorias; el
  agente `bautizador` vela por eso, no por traducir nada.
- Calidad de código: antes de comitear una tarea, pasar por los agentes
  `minimalista` (simplicidad, sin código de más), `coherencia-ui` (solo si el
  cambio toca `apps/web`), `bautizador` (nombres), `documentador` (docs y
  comentarios) y `mapeador` (mapa Mermaid del proyecto), en ese orden — o usar
  la skill `/revision-lucia` que los encadena.
- Mapa del proyecto: `docs/06-mapa-del-proyecto.md` tiene los diagramas Mermaid
  (flujo general, módulos, secuencias) y la tabla de qué RF vive en qué
  archivo. Consultarlo antes de tocar algo que no se conoce; lo mantiene el
  agente `mapeador`.
- Coherencia de interfaz: `docs/07-coherencia-ui.md` tiene los criterios (C-1 a
  C-7) y el inventario de incumplimientos abiertos. Recorrerlos antes de
  comitear cualquier cambio en `apps/web`; una incoherencia que no se arregle
  en el mismo commit se apunta en el inventario.
- Versión y alcance: `docs/02-requerimientos.md` tiene el alcance congelado de
  v1.0 (todo lo que ya está ahí, con la fecha de corte); un RF/RNF añadido
  después va a su sección `Post 1.0 (futuro)`. `CHANGELOG.md` lleva el
  historial de versiones. Lo vigila el agente `versionador` — usar `/versionar`
  al cerrar una fase del roadmap o al añadir un requerimiento nuevo.
- Comandos: `make doctor`, `make up` (`S=api`/`S=web`), `make engines`, `make test`, `make lint`.
- Licencia GPL-3.0: toda dependencia nueva debe ser compatible.
