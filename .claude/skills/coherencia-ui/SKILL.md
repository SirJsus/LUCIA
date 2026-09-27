---
name: coherencia-ui
description: Verifica que las pantallas de apps/web sean coherentes entre sí y cumplan los criterios C-1 a C-7 de docs/07-coherencia-ui.md (paridad teclado/pantalla, mismos nombres, estados del sistema visibles, componentes compartidos, accesibilidad). Usar al construir o cambiar una pantalla, o con "todo" para barrer las seis de una vez.
---

Invoca al agente `coherencia-ui` (Agent tool, `subagent_type: "coherencia-ui"`).

- Sin `args`, o con un alcance concreto: **modo pantalla**, sobre el `git diff`
  actual o lo que indique el usuario.
- Con `args` que pidan un barrido (`todo`, `todas`, `completo`): **modo barrido
  completo**, las seis pantallas contra los siete criterios, dejando el
  inventario de `docs/07-coherencia-ui.md` reconstruido entero.

Espera su reporte y muéstraselo al usuario con sus tres secciones: qué corrigió,
qué queda para que decida él, y cuántas filas del inventario quedan abiertas.
