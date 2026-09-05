---
name: documentar
description: Actualiza la documentación de LUCIA (docs/, README, ADRs) y comenta el código cambiado explicando qué hace y cómo interactúa con otros módulos. Usar después de implementar una feature, endpoint o módulo nuevo, o al tomar una decisión de arquitectura.
---

Invoca al agente `documentador` (Agent tool, `subagent_type: "documentador"`)
pasándole como alcance el `git diff` actual (o el que indique el usuario en `args`).
Espera su reporte de documentos y archivos actualizados, y muéstraselo al usuario
resumido.
