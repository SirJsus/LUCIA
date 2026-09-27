---
name: versionar
description: Revisa el alcance de v1.0 frente a docs/02-requerimientos.md y docs/05-roadmap.md, mueve requerimientos nuevos a Post 1.0 si corresponde, y mantiene sincronizado el número de versión (pyproject.toml, package.json, __version__, CHANGELOG.md) en todo el repo. Usar al cerrar una fase del roadmap, al añadir un requerimiento nuevo, o para pedir explícitamente un cambio de versión.
---

Invoca al agente `versionador` (Agent tool, `subagent_type: "versionador"`)
pasándole el alcance indicado por el usuario en `args`, o el `git diff` actual si
no se indica nada. Espera su reporte (alcance movido, versión anterior → nueva y
motivo, o "sin cambios") y muéstraselo al usuario resumido.
