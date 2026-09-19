# ADR-0016 · Las agregaciones estadísticas se hacen en SQL, no en polars

**Estado:** aceptado · **Fecha:** 2026-09-19

## Contexto

[ADR-0005](0005-sqlite-local-first.md), al elegir SQLite, dejó escrita esta
consecuencia: *"Agregaciones pesadas se hacen en polars sobre extractos, no con
SQL complejo"*. [ADR-0003](0003-python-orquesta-cpp-motores.md) apoyaba la
elección de Python citando su ecosistema de datos, polars incluido, y
[04-stack-tecnologico.md](../04-stack-tecnologico.md) lo listaba como la
herramienta de agregación del proyecto. `polars>=1.5` estaba declarado en
`packages/core/pyproject.toml` desde el primer día.

Nunca se usó. Todo RF-3 —el dashboard, el rendimiento por apertura y por fase,
los tipos de error, los tramos de reloj, las tendencias temporales— se escribió
en SQL con SQLAlchemy, en `apps/api/lucia_api/services/stats.py`, y lo que no
cabía en una consulta se resolvió recorriendo las jugadas ya cargadas en
`packages/core/lucia_core/insights/`. La auditoría de cierre de la fase 2
(2026-09-19) lo destapó: una dependencia declarada, bloqueada en el lockfile e
instalada en cada entorno, sin un solo `import` en todo el repositorio.

Quedaban dos salidas: cumplir la consecuencia de ADR-0005 reescribiendo las
agregaciones en polars, o reconocer que la decisión de 2026-09-05 no se sostuvo
y quitar la dependencia.

## Decisión

**Las agregaciones se quedan en SQL.** Se elimina `polars` de
`packages/core/pyproject.toml`. Este ADR deja sin efecto esa consecuencia de
ADR-0005, que no se edita.

## Razones

- **El volumen no lo pedía.** La premisa de ADR-0005 —"agregaciones pesadas"—
  no se dio: el historial de un jugador son miles de partidas, no millones, y
  SQLite las agrupa sin despeinarse. Se adoptó una herramienta para un problema
  de escala que este proyecto no tiene (RNF-7: base local de un solo usuario).
- **Un solo lenguaje para leer la base.** Mezclar SQL y un dataframe obliga a
  decidir, en cada consulta nueva, dónde cae la frontera; y esa frontera se
  habría movido con cada ítem. Que RF-3 entero esté en SQL hace que una
  agregación nueva se parezca a las que ya hay.
- **Una dependencia sin usar no es gratis.** polars arrastra un binario
  compilado por plataforma, y este proyecto tiene que empaquetarse para Linux,
  macOS y Windows (RNF-4). Peso e instalación a cambio de nada.
- **Es reversible.** Si una agregación futura —RF-3.8, rivales recurrentes— no
  cabe en SQL, volver a añadirla es una línea en `pyproject.toml`. La decisión
  que este ADR toma no es "polars nunca", es "hoy no hace falta y no se declara
  lo que no se usa".

## Consecuencias

- La consecuencia de ADR-0005 sobre polars queda **superada por este ADR**.
  ADR-0003 sigue siendo válido en lo que decide —Python orquesta, C++ calcula—;
  solo pierde uno de los ejemplos de su razonamiento.
- `04-stack-tecnologico.md` deja de listar polars entre las tecnologías del
  backend, con nota de por qué.
- Cualquier agregación nueva se escribe en SQL en `services/stats.py`, o
  recorriendo jugadas ya cargadas en `lucia_core.insights`, que son los dos
  caminos que RF-3 dejó hechos.
