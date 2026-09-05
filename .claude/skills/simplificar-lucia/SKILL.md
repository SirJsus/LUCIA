---
name: simplificar-lucia
description: Revisa el código cambiado en LUCIA para maximizar simplicidad y legibilidad y minimizar la cantidad de código, evaluando duplicación entre packages/core, packages/chesscom, apps/api y apps/web, y uso de las dependencias ya elegidas en el stack. Usar antes de comitear o cuando una tarea haya crecido más de lo esperado.
---

Invoca al agente `minimalista` (Agent tool, `subagent_type: "minimalista"`) pasándole
como alcance el `git diff` actual (o el que indique el usuario en `args`). Espera su
reporte de simplificaciones aplicadas y de sugerencias discutibles, y muéstraselo al
usuario resumido.
