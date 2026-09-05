---
name: revision-lucia
description: Pasa el código cambiado en LUCIA por los cuatro agentes de calidad del proyecto en cadena, simplificar, bautizar, documentar y mapear, antes de comitear. Usar como revisión final de una tarea de código completa.
---

Ejecuta en este orden, cada uno sobre el resultado del anterior (el `git diff`
crece o cambia entre pasos, vuelve a calcularlo antes de cada agente):

1. **`minimalista`** — simplificar primero; no tiene sentido nombrar, documentar
   o mapear código que se va a borrar o fusionar.
2. **`bautizador`** — nombrar bien la forma final del código.
3. **`documentador`** — documentar la forma final, ya simplificada y bien
   nombrada (docs/, README, ADRs, comentarios).
4. **`mapeador`** — cruzar el resultado de los tres anteriores en
   `docs/06-mapa-del-proyecto.md`: actualiza sus diagramas Mermaid y la tabla de
   ubicación con los nombres, la estructura y los RF/ADR que dejaron los pasos
   previos.

Invoca cada uno con el Agent tool (`subagent_type` correspondiente). Al final,
presenta al usuario un resumen único con cuatro secciones (Simplificación /
Nombres / Documentación / Mapa), no cuatro reportes sueltos.
