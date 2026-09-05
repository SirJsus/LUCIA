---
name: mapear
description: Actualiza el mapa del proyecto en docs/06-mapa-del-proyecto.md (diagramas Mermaid y tabla de ubicación por requerimiento) tras un cambio estructural. Usar después de añadir/mover/renombrar módulos, endpoints o flujos, o después de correr /simplificar-lucia, /bautizar o /documentar.
---

Invoca al agente `mapeador` (Agent tool, `subagent_type: "mapeador"`) pasándole
como alcance el `git diff` actual (o el que indique el usuario en `args`). Espera
su reporte de qué diagramas o filas se actualizaron y muéstraselo al usuario
resumido.
