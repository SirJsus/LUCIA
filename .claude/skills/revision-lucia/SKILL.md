---
name: revision-lucia
description: Pasa el código cambiado en LUCIA por los agentes de calidad del proyecto en cadena, simplificar, coherencia de interfaz (solo si toca apps/web), bautizar, documentar y mapear, antes de comitear. Usar como revisión final de una tarea de código completa.
---

Ejecuta en este orden, cada uno sobre el resultado del anterior (el `git diff`
crece o cambia entre pasos, vuelve a calcularlo antes de cada agente):

1. **`minimalista`** — simplificar primero; no tiene sentido nombrar, documentar
   o mapear código que se va a borrar o fusionar.
2. **`coherencia-ui`** — **solo si el diff toca `apps/web`**; si no, sáltalo y
   dilo en el resumen. Va aquí, después de simplificar y antes de nombrar,
   porque puede sustituir mensajes escritos a mano por los componentes
   compartidos y unificar etiquetas: lo que deje escrito todavía tiene que
   pasar por `bautizador` y `documentador`.
3. **`bautizador`** — nombrar bien la forma final del código.
4. **`documentador`** — documentar la forma final, ya simplificada y bien
   nombrada (docs/, README, ADRs, comentarios).
5. **`mapeador`** — cruzar el resultado de los anteriores en
   `docs/06-mapa-del-proyecto.md`: actualiza sus diagramas Mermaid y la tabla de
   ubicación con los nombres, la estructura y los RF/ADR que dejaron los pasos
   previos.

Invoca cada uno con el Agent tool (`subagent_type` correspondiente). Al final,
presenta al usuario un resumen único con una sección por agente que haya
corrido (Simplificación / Interfaz / Nombres / Documentación / Mapa), no varios
reportes sueltos.
