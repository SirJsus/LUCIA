# ADR-0009 · La tabla de aperturas se versiona ya procesada, no se descarga al instalar

**Estado:** aceptado · **Fecha:** 2026-09-09

## Contexto

Nombrar la apertura de una partida (RF-3.2) y marcar como teoría las jugadas
que siguen en el libro (la categoría "Libro" de RF-2.2) necesita una tabla ECO:
una lista de líneas con su código y su nombre. La fuente elegida es
[chess-openings de Lichess](https://github.com/lichess-org/chess-openings),
**CC0 1.0 (dominio público)**, ya listada como fuente externa en
[04-stack-tecnologico.md](../04-stack-tecnologico.md): son cinco TSV, uno por
volumen ECO, con `eco`, `name` y el `pgn` de la línea.

Esa tabla es un dato de terceros que hay que traer de algún sitio, y el
repositorio ya tenía dos costumbres opuestas para eso:

- los **motores** no se versionan: son sub-módulos que se compilan
  ([ADR-0002](0002-motores-como-submodulos.md)),
- y las **redes de Lc0** tampoco: las descarga `scripts/setup-engines.sh` y
  `.gitignore` las excluye (`engines/networks/`), porque pesan decenas de MB.

Las opciones eran tres:

1. **Descargar los TSV de Lichess al instalar** (o la primera vez que hiciera
   falta), como con las redes.
2. **Versionar los cinco TSV de Lichess tal cual** y procesarlos al arrancar.
3. **Versionar el resultado de procesarlos**: una fila por posición, en EPD.

## Decisión

**La opción 3.** Se versiona
`packages/core/lucia_core/openings/data/openings.tsv`, generado a partir de la
fuente: 3.810 posiciones con su código ECO y su nombre, ~420 KB de texto. Lo
que se guarda es la **posición** (EPD: el FEN sin los contadores), no la
secuencia de jugadas que lleva a ella.

`scripts/build-openings-table.py` es el único punto del proyecto que habla con
Lichess, y solo se ejecuta a mano para actualizar la tabla cuando la fuente
cambie. Acepta `--from-dir` para regenerarla desde una copia local, sin red.

## Razones

- **RNF-1, local-first.** La aplicación funciona offline tras la importación
  inicial. Con la opción 1, una instalación sin red se quedaría sin nombres de
  apertura y sin categoría "Libro" —no fallando, que sería honesto, sino
  callando—, y el fallo aparecería meses después, al reinstalar en otra máquina.
  Descargar en el primer uso es peor todavía: convierte una función del núcleo
  en algo que a veces está y a veces no.
- **No es comparable a las redes de Lc0.** El criterio para no versionar allí
  es el peso: decenas de MB de binario opaco por red. Aquí son 420 KB de texto,
  diffeable, que cambia unas pocas veces al año. El coste de tenerlo en el
  repositorio es menor que el de una dependencia de red en tiempo de ejecución.
- **Procesado, porque reproducir 3.810 partidas al arrancar cuesta segundos.**
  La opción 2 obligaría a `lucia_core.openings` a recorrer los PGN de todas las
  líneas cada vez que se importa el módulo, y a llevar esa lógica al núcleo. La
  transformación es determinista y solo cambia con la fuente: es exactamente lo
  que tiene sentido hacer una vez y guardar.
- **La clave por posición es lo que hace útil la tabla.** Guardar el EPD y no la
  secuencia de jugadas hace que las transposiciones se reconozcan solas: llegar
  a la Najdorf por otro orden de jugadas es la misma posición y sale con el
  mismo nombre. Con la lista original habría que reconocerlo a mano.
- **La licencia lo permite sin condiciones.** CC0 es dominio público: no exige
  atribución ni impone términos al derivado (RNF-5,
  [ADR-0004](0004-licencia-gpl3.md)). Aun así se atribuye —en el README, en la
  cabecera del TSV generado y en el script—, porque es lo decente y porque
  quien encuentre el archivo dentro de un paquete GPL tiene que poder saber de
  dónde salió y que no está bajo GPL.

## Consecuencias

- **La tabla envejece en silencio.** Si Lichess añade líneas, aquí no llegan
  hasta que alguien ejecute el script y comitee el resultado. Es aceptable:
  una apertura sin nombre nuevo no rompe nada, y la alternativa era depender de
  la red. Actualizarla es un commit con un diff legible.
- **`.gitignore` tuvo que dejar de ignorar este `data/`.** La regla era `data/`,
  pensada para la base SQLite de la raíz, y se tragaba también este directorio:
  ahora es `/data/`, anclada a la raíz. Un archivo de datos que "se versiona a
  propósito" dentro de un paquete Python es lo bastante raro como para que la
  próxima regla de ignorados vuelva a pisarlo; el comentario del `.gitignore`
  lo avisa.
- **El paquete `lucia-core` lleva datos, no solo código.** Cualquier forma de
  empaquetarlo tiene que incluir `lucia_core/openings/data/`. Con hatchling y
  `packages = ["lucia_core"]` entra solo, pero deja de ser cierto que el
  paquete sean únicamente `.py`.
- **La tabla tiene huecos y el consumidor los asume.** No es consecuencia de
  versionarla sino de la fuente —solo nombra las posiciones donde termina
  alguna línea con nombre—, pero se hereda tal cual: `identify_opening` tolera
  rachas cortas de posiciones desconocidas y se queda con la más profunda. Está
  contado en `lucia_core.openings`.
- **RF-3.6 no queda cubierto por esto.** Comparar el repertorio propio con la
  teoría de maestros usa el Lichess Opening **Explorer**, que es una API y sí
  necesita red. Esta tabla da nombres, no estadísticas de partidas; cuando
  llegue RF-3.6 habrá que decidir aparte qué pasa sin conexión, y esa decisión
  no la fija este ADR.
- **Qué NO fija.** De dónde sale la tabla (podría cambiarse la fuente por otra
  compatible sin tocar nada más que el script) ni cómo se busca dentro de ella;
  fija que el artefacto vive en el repositorio y que la aplicación no descarga
  nada para usarlo.

## Ver también

- RF-2.2 y RF-3.2 en [02-requerimientos.md](../02-requerimientos.md), con la
  nota de cómo se cumplieron.
- [ADR-0004](0004-licencia-gpl3.md): compatibilidad de licencias (CC0 lo es).
- [ADR-0002](0002-motores-como-submodulos.md): la costumbre contraria, y por
  qué allí sí.
- `scripts/build-openings-table.py` (la genera) y
  `packages/core/lucia_core/openings/__init__.py` (la lee).
