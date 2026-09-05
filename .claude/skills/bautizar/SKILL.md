---
name: bautizar
description: Revisa y corrige los nombres (variables, funciones, clases, módulos, archivos, endpoints, columnas de BD) del código cambiado en LUCIA para que sean claros, explícitos y en español. Usar antes de comitear código nuevo o cuando un nombre resulte ambiguo o genérico.
---

Invoca al agente `bautizador` (Agent tool, `subagent_type: "bautizador"`) pasándole
como alcance el `git diff` actual (o el que indique el usuario en `args`). Espera su
reporte de renombres y muéstraselo al usuario de forma resumida: nombre anterior →
nombre nuevo → motivo.
