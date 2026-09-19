# ADR-0015 · Cada motor se configura en sus propios términos: opciones filtradas, esfuerzo en su unidad y la red dentro de su identidad

**Estado:** aceptado · **Fecha:** 2026-09-06 *(escrito el 2026-09-19, al
auditar la documentación de la fase 2: la decisión estaba tomada y razonada en
el código y en el roadmap, pero no registrada como ADR)*

## Contexto

RF-2.6 pide a Lc0 como segunda opinión junto a Stockfish, y RNF-9 pide que
cualquier motor UCI se pueda enchufar sin cambiar el núcleo. Hasta la fase 2
LUCIA tenía un solo motor de verdad: `EngineBridge` mandaba `Threads` y `Hash`
a lo que hubiera al otro lado del tubo y le pedía "profundidad N".

Con Lc0 eso se rompe por tres sitios a la vez, y los tres son del mismo tipo:
dábamos por universal lo que era de Stockfish.

1. **Las opciones no son universales.** Lc0 no tiene `Hash` —usa
   `NNCacheSize`, medido en posiciones y no en MB, que no es un equivalente— y
   mandarle una opción que no declara aborta la conexión. Lc0 no llegó a
   funcionar nunca por esto.
2. **La unidad de esfuerzo no es universal.** Stockfish busca alfa-beta y
   "profundidad 18" es una cantidad de trabajo reconocible. Lc0 explora con
   MCTS: la profundidad es un promedio del árbol y pedir una concreta cuesta un
   número imprevisible de evaluaciones de red. Lo predecible ahí es acotar
   nodos.
3. **El binario no identifica al evaluador.** La evaluación de Lc0 la da su
   red neuronal: el mismo `lc0` con otra red responde otra cosa para la misma
   posición, y la caché de posiciones de RF-2.7 estaba indexada solo por el
   nombre del motor.

## Decisión

**El motor decide cómo se le habla; el resto de la aplicación no se entera.**

- **Las opciones genéricas se aplican solo si el motor las declara**
  (`EngineBridge._options_to_apply`, contra `engine.options` de python-chess).
  Las `extra_options` que alguien pidió expresamente se mandan sin filtrar: si
  no existen es un error de configuración y conviene que se note.
- **La unidad del límite se deriva del motor, no se configura**
  (`EffectiveEngineConfig.limit_kind`: `nodes` para Lc0, `depth` para el
  resto). El valor sigue siendo un número editable en RF-5.4; lo que cambia
  con el motor es su rango y su significado.
- **En la clave de `position_cache`, "motor" incluye la red**
  (`lc0/744706-conv.pb.gz`). El valor del límite sigue guardándose en la
  columna `depth`, sin ambigüedad: la unidad se deduce del motor, que ya es
  parte de la clave.
- **Las posiciones terminales no se le preguntan a ningún motor**
  (`lucia_core.analysis.evaluate_positions`): su evaluación se deduce (mate o
  tablas).

## Razones

- **Filtrar es más barato que catalogar.** La alternativa era una tabla de
  "qué opciones acepta cada motor" mantenida a mano, que se queda vieja en la
  siguiente versión de cualquiera de ellos. El propio motor ya publica su
  lista al arrancar; preguntársela es lo que hace que un motor UCI
  desconocido funcione sin tocar el núcleo (RNF-9).
- **Una unidad común habría mentido.** Traducir nodos a profundidad, o pedir
  profundidad a Lc0 "porque es lo que entiende la interfaz", da tiempos de
  análisis imprevisibles: 1.600 nodos es un esfuerzo normal en Lc0 e imposible
  como profundidad en Stockfish. Se vio en la validación del formulario, que
  compartía rango para los dos.
- **Una caché que ignora la red devuelve datos de otro evaluador**, y
  silenciosamente: pasó al cambiar de red, con las evaluaciones de la anterior
  saliendo como si fueran nuevas. Lo mismo vale para las alternativas
  rescatadas de ahí ([ADR-0007](0007-alternativas-por-jugada-json-y-cache.md)):
  la clave tiene que ser exacta o no sirve.
- **Preguntar en una posición terminal no es una rareza teórica**: cualquier
  partida acabada en mate terminaba ahí, y Lc0 se queda esperando
  indefinidamente porque no hay jugada que devolver. Deducirlo es además más
  correcto que evaluarlo.

## Consecuencias

- **Añadir un tercer motor UCI no toca `lucia_core`**, pero sí dos sitios del
  producto: su ruta en `.env` (nunca por HTTP — sería ejecución arbitraria) y
  su nombre en `ENGINE_NAMES` de `apps/api/lucia_api/services/engines.py`, con
  su unidad de esfuerzo si no es profundidad. RNF-9 se cumple en el núcleo,
  que es lo que el requerimiento pide; el catálogo de motores del producto
  sigue siendo una lista corta y escrita.
- **La configuración de RF-5.4 no es la misma para todos los motores**: el
  campo "esfuerzo" cambia de unidad y de rango según cuál se edite, y la
  interfaz tiene que decir cuál es.
- **La caché queda particionada por red.** Cambiar la red de Lc0 no invalida
  nada, pero tampoco reaprovecha: las posiciones se vuelven a evaluar. Es lo
  correcto y conviene saberlo antes de cambiarla a mitad de un lote.
- **Comparar dos motores es comparar dos análisis terminados**
  (`GET /analysis/compare`), en la unidad común de RF-2.3 (probabilidad de
  victoria) y no en la W/D/L nativa de Lc0, que no se lee. Ver la nota de
  RF-2.6 en [02-requerimientos.md](../02-requerimientos.md).
- **Qué NO fija.** Ni que el límite tenga que ser una sola magnitud por motor
  para siempre, ni que la W/D/L de Lc0 no se pueda persistir más adelante:
  sería una columna más en `analyzed_moves`, sin tocar esta decisión.

## Ver también

- RF-2.6, RF-2.7 y RNF-9 en [02-requerimientos.md](../02-requerimientos.md).
- [ADR-0002](0002-motores-como-submodulos.md) (de dónde salen los binarios y
  las redes) y [ADR-0003](0003-python-orquesta-cpp-motores.md) (por qué se
  habla UCI y no se enlaza nada).
- `packages/core/lucia_core/engine/bridge.py`,
  `apps/api/lucia_api/services/engines.py` (`limit_kind`,
  `uci_extra_options`), `apps/api/lucia_api/services/analysis.py`
  (`CachedEngineBridge`, `_cache_engine_name`) y
  `packages/core/lucia_core/analysis/__init__.py` (`_terminal_score`).
