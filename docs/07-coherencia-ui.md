# 07 · Coherencia de interfaz

Este documento existe porque la aplicación creció pantalla a pantalla y cada
una resolvió a su manera cosas que deberían resolverse igual en todas. El
síntoma que lo motivó: en el detalle de una partida se navegaba con botones en
pantalla y la interfaz cambiaba según lo que estuviera haciendo el motor,
mientras que en el tablero de análisis se navegaba solo con el teclado y la
pantalla era siempre la misma. Quien ya sabe de análisis de partidas se adapta;
quien no, leía el tablero de análisis como una herramienta tosca. Eso ya está
corregido —las 38 filas que motivaron este inventario se cerraron el
2026-09-08—, pero los criterios siguen vigentes: son la vara con la que se mide
cada cambio nuevo de `apps/web`. El barrido completo que se hizo ese mismo día
para comprobar que no quedaba nada destapó nueve incumplimientos más, las filas
39 a 47, cerradas también ese día. La revisión de RF-10.2 —las alternativas por
jugada del visor, ese mismo 2026-09-08— abrió otras cuatro, de la 48 a la 51,
cerradas igualmente. La revisión de los extractores de patrones (RF-2.8,
RF-3.4, RF-3.5, RF-3.2) abrió dos más el 2026-09-09, la 52 y la 53, cerradas
también. Ese mismo día, la tabla ECO propia (RF-3.2) puso en pantalla por
primera vez la categoría "Teoría" de la clasificación de jugadas, que estaba
definida desde el principio pero no se producía nunca, y con ella las filas 54
y 55, cerradas también. La barra de filtros de Partidas (RF-5.3), que ese mismo
2026-09-09 pasó de cuatro filtros a nueve, abrió las filas 56 a 60, cerradas
ese mismo día. La comparación de repertorio (RF-3.6), del 2026-09-10, abrió las
filas 61 a 63, cerradas también. La importación de un PGN de otra fuente
(RF-1.5), del 2026-09-17, abrió las filas 64 a 67: la 64 y la 66 se cerraron ese
mismo día y quedan abiertas la 65 y la 67. La exportación del análisis a PGN
anotado (RF-5.5), del mismo día, abrió las filas 68 a 70, las tres sobre el
mismo control del visor. Las tendencias temporales del panel de estadísticas
(RF-3.7), del 2026-09-18, abrieron las filas 71 a 73 y las tres se cerraron ese
mismo día. Abrir una partida como tablero y traer un PGN pegado (RF-6.6 y
RF-6.7), del mismo 2026-09-18, abrieron las filas 74 a 77, cerradas ese mismo
día. Deshacer y rehacer (RF-6.8) y el análisis completo del tablero (RF-6.9),
del mismo día, abrieron las filas 78 a 82 —todas de la misma raíz: el tablero
de análisis hace ya lo mismo que el visor y lo enseñaba en otro sitio y con
otra forma— y se cerraron también, y con ellas la 69, que llevaba abierta
desde RF-5.5. El editor de posición pieza a pieza —lo que faltaba de RF-6.1,
del mismo 2026-09-18— abrió las filas 83 a 85 y las tres se cerraron ese mismo
día. Marcar un tablero como partida propia (RF-6.5), del mismo día, dejó de ser
una casilla y pasó a ser un formulario de cuatro campos, y abrió las filas 86 y
87, cerradas también ese mismo día. La capa de ocupación del tablero (RF-7.1 a
RF-7.7), del 2026-09-19, abrió las filas 88 a 90, cerradas también ese mismo
día. Ese mismo 2026-09-19, recorriendo el apéndice de la fase 2, se cerraron las
**cuatro que quedaban abiertas** —la 65 y la 67 de Partidas, la 68 y la 70 del
control de exportar del visor—, algunas desde el 2026-09-17. Vacío es como
debería encontrarse este documento siempre que se lea, y por primera vez lo
está: eso no lo convierte en un estado alcanzado, sino en el estado del que se
parte la próxima vez.

**Qué es cada mitad de este documento.** Los criterios C-1 a C-7 son
**RNF-11**, que vive en la sección Post 1.0 de
[docs/02-requerimientos.md](02-requerimientos.md): son una práctica de trabajo
vinculante desde hoy en cada commit de `apps/web`, no una prestación que se
entregue en v1.0, y por eso no cuentan para el progreso hacia 1.0.0. El
inventario es otra cosa: incumplimientos concretos, con archivo y línea. Las 38
primeras filas lo eran de requerimientos **ya congelados** (RF-5.1, RF-5.2,
RF-6.2, RNF-6), y por eso se arreglaron dentro de v1.0, en la fase 2 de
[docs/05-roadmap.md](05-roadmap.md). Las nueve últimas (39 a 47) eran de dos
clases, y la distinción sigue siendo útil para el próximo barrido: de la 39 a
la 41 eran recetas de estilo copiadas a mano —no se veía nada raro en pantalla,
pero una coherencia que sostiene el copiar y pegar se rompe en el primer
cambio—, y de la 42 a la 47, cosas que se notaban usando la aplicación.

No es una lista de gustos: son criterios verificables. La revisión es manual,
antes de comitear cambios de front — ver [Cómo se verifica](#cómo-se-verifica).

## Criterios

| ID | Criterio |
| ---- | ---------- |
| C-1 | **Paridad teclado ↔ pantalla.** Toda acción disponible por teclado tiene un control visible equivalente, y los atajos se anuncian en la interfaz en vez de darse por sabidos. El teclado es un acelerador, nunca la única vía. |
| C-2 | **Misma acción, mismo nombre, mismo sitio.** Una acción que existe en dos pantallas se llama igual, se ve igual y ocupa la misma posición relativa. |
| C-3 | **La interfaz refleja lo que el sistema está haciendo.** Toda pantalla que dependa del motor o de la red distingue visualmente: inactiva, en cola, trabajando (con progreso si se conoce), terminada, vacía y con error. No basta un "analizando…" en letra pequeña. |
| C-4 | **Estados compartidos, no artesanales.** Carga, error y vacío se resuelven con `Spinner`, `ErrorBox` y `EmptyState` de `apps/web/src/components/Feedback.tsx`. Nada de frases sueltas en texto plano para lo mismo. |
| C-5 | **Un dato, una forma.** La evaluación, la clasificación de jugada y el nombre del motor se presentan igual en todas partes: mismo signo, misma unidad, mismo punto de vista (blancas) y mismo formateador (`lib/score.ts`). |
| C-6 | **Legible sin saber de ajedrez.** Todo número del motor va acompañado de etiqueta, leyenda o representación visual. `+0.35` solo, sin más, no comunica nada a quien no lee evaluaciones. |
| C-7 | **Accesibilidad mínima.** Foco visible, `aria-label` en los botones que son solo icono, y ningún significado transmitido únicamente por color. |

## Inventario de incoherencias abiertas (al 2026-09-19)

**Ninguna.** Es como debería encontrarse siempre este inventario, y por primera
vez desde que se abrió lo está: las últimas cuatro —la 65 y la 67 de la pantalla
de Partidas, la 68 y la 70 del control de exportar del visor— se cerraron el
2026-09-19, al recorrer el apéndice de la fase 2. Los números no se renumeran al
cerrar una fila, que es la referencia con la que se habla de ella en un commit.

La tabla se queda aquí, vacía, porque el sitio donde se apunta un incumplimiento
nuevo no debería haber que inventarlo.

| # | Incoherencia | Dónde | Criterio |
| --- | --- | --- | --- |

## Lo que se cerró

Las 90 filas de este inventario, que están todas cerradas, se cerraron en doce
pasadas, y aquí queda el rastro de qué se hizo, para que un
`git blame` no sea la única forma de averiguarlo.

**2026-09-06 · legibilidad del análisis.** Apareció la barra de evaluación, el
tablero de análisis empezó a dibujar las flechas del motor, los vacíos del
panel lateral pasaron a ser `EmptyState` y los botones de solo icono ganaron
nombre accesible.

**2026-09-07 · cimientos compartidos.** Salieron los componentes que faltaban
—`Button`, `Panel`, `BoardWithEvalBar`, `MoveNavigator`, `SuccessBox`,
`WarningBox`, `ProgressBox`— y las recetas de clases de `components/styles.ts`;
los formateadores se juntaron en `lib/format.ts`; y las piezas de tablero se
mudaron de `features/viewer/` a `components/board/`.

**2026-09-08 · el resto.** La pasada que cerró las 38 filas:

- **Paridad teclado ↔ pantalla (C-1).** El tablero de análisis tiene los
  mismos controles de navegación que el visor (`MoveNavigator`) y los mismos
  cuatro atajos, `Home` y `End` incluidos; las dos pantallas anuncian los suyos
  en una frase bajo el tablero, con la misma forma
  (`BOARD_HINT_CLASSES`). Promover y borrar una variante dejaron de vivir solo
  en `group-hover`: están siempre, atenuadas, y se realzan al señalar o al
  enfocar.
- **Misma acción, mismo nombre, mismo sitio (C-2).** Las cabeceras de las dos
  pantallas de tablero ordenan igual sus acciones (girar tablero · motor ·
  acción principal), y "Partida propia" bajó con el título, que es donde vive
  una propiedad del tablero. El enlace del listado dice "Ver partida", que es
  lo que hace. Filtrar por jugador se aplica al teclear en las dos pantallas
  que lo tienen. Destruir se llama "Eliminar" en los dos sitios y los dos
  preguntan antes. Y el control más repetido de la aplicación —el botón que
  lleva a una posición, que estaba copiado en la lista de jugadas, el árbol de
  variantes y las líneas del motor— es uno solo
  (`components/board/MoveButton.tsx`), igual que los atajos que lo acompañan
  (`components/board/useMoveNavigationKeys.ts`).
- **La interfaz refleja lo que hace el sistema (C-3).** El panel del motor
  distingue apagado, buscando, con error, sin líneas y con líneas; el
  autoguardado tiene estado de error; marcar "Partida propia" y "Copiar PGN"
  dicen si salieron bien o mal; y un fallo al consultar los análisis previos ya
  no se lee como "Sin analizar".
- **Estados compartidos (C-4).** Ya no queda ninguna receta de `EmptyState`
  copiada a mano.
- **Un dato, una forma (C-5).** La numeración de jugadas sale de
  `lib/moves.ts` en las cinco pantallas que numeran, y parte de la posición
  real de la partida: una que empieza en la jugada 12 se numera desde 12 en la
  lista, en el gráfico y en la comparación de motores. El gráfico dejó de
  contar medias jugadas. Las medidas del panel lateral y de las listas
  navegables son una sola (`BOARD_SIDEBAR_GRID_CLASS`,
  `MOVE_LIST_HEIGHT_CLASS`), y los títulos de pantalla, un solo tamaño.
- **Legible sin saber de ajedrez (C-6).** La columna de evaluación del panel
  del motor tiene encabezado; MultiPV se explica donde se enseña; "pts de
  diferencia" dice de qué; el eje del gráfico dice qué mide; y el visor y el
  listado avisan de las partidas que no empiezan en la posición estándar, con
  el campo `starts_from_custom_position` que la API calcula del PGN.
- **Accesibilidad mínima (C-7).** Nada se transmite ya solo por color: la
  clasificación de jugada viaja con su nombre (`ClassificationBadge`), las
  victorias/tablas/derrotas llevan su letra, la fase que más cuesta se dice con
  palabras además de pintarse, y la barra de evaluación gira sus colores con el
  tablero en vez de contradecir al motor. El tooltip y los ejes de los tres
  gráficos tienen paleta propia en tema oscuro (`lib/chartTheme.ts`).
- **Y una que era un defecto, no una incoherencia:** en el panel del motor,
  pulsar cualquier jugada de una línea lleva el tablero hasta ahí. Antes solo
  la primera hacía algo, con el mismo aspecto que las demás.

**2026-09-08 · el barrido de comprobación.** Recorrer las seis pantallas contra
los siete criterios, ya con las 38 cerradas, destapó nueve incoherencias más
(las filas 39 a 47) y once arreglos mecánicos. Las nueve, cerradas el mismo
día:

- **Tres recetas que se sostenían copiando y pegando** (C-2), y que ya habían
  divergido: la insignia sale ahora de `components/Badge.tsx` —seis sitios, con
  tres rellenos distintos entre ellos—, las tres tablas de la aplicación de
  `components/DataTable.tsx`, y el desplegable de motor de
  `components/EngineSelect.tsx`, que además tenía dos textos de ayuda
  distintos para lo mismo.
- **Abrir un elemento de un listado** se hace igual en los dos que hay (C-2):
  un enlace con aspecto de botón al final de la fila —"Ver partida", "Ver
  tablero"—, separado de eliminar. En Tableros era el título entero.
- **El filtro por jugador** está en el mismo sitio en las dos pantallas que lo
  tienen (C-2): una barra de filtros bajo el título, no en la cabecera.
- **La navegación marca la sección también en las pantallas de detalle**
  (C-2): en el visor de una partida no se iluminaba nada, mientras que en el
  tablero de análisis sí se iluminaba "Tableros".
- **El tablero de análisis dice cuándo su evaluación es de otra posición**
  (C-3). Mientras corre el retardo de 400 ms, el panel del motor y la barra
  enseñaban lo de la posición anterior sin avisar: la barra llegaba a
  contradecir al tablero durante una secuencia rápida de jugadas.
- **La comparación de motores dice qué es cada número** (C-6), con la misma
  solución que ya usaba el panel del motor: una línea que lo explica antes de
  enseñarlos.
- **Los tableros avisan de que no empiezan en la posición estándar** (C-6),
  que es el caso normal de uno creado desde un FEN. Es la misma insignia del
  listado de partidas y del visor.

Y los once arreglos mecánicos del mismo barrido, que no llegaron a ser fila
porque no había nada que decidir:

- **C-1.** Las flechas del teclado dejan de robarle la pulsación al desplegable
  de motor: `useMoveNavigationKeys` ya ignoraba `input` y `textarea`, y ahora
  también `select`. Antes, con el foco ahí, una flecha cambiaba de motor **y**
  movía el tablero.
- **C-7.** El desplegable de motor del visor no tenía nombre accesible; el del
  tablero de análisis sí.
- **C-3.** Borrar un tablero no decía nada mientras la petición viajaba (ahora
  "Eliminando…", como el resto de escrituras), y la pantalla de Motores seguía
  diciendo "Configuración guardada" al lado de valores ya editados.
- **C-4.** "No hay diferencias de valoración relevantes" era la última frase
  suelta que hacía de vacío; ahora es un `EmptyState`.
- **C-5.** El eje "Partidas por mes" componía la fecha a mano; sale de
  `formatYearMonth` en `lib/format.ts`. Y los dos desplegables de motor tenían
  los nombres escritos a mano en vez de pasar por `formatEngineName`: salen de
  `ENGINE_IDS`.
- **C-2.** El botón de cada discrepancia de la comparación de motores tenía su
  propia receta de clases, con otro borde y otro `hover` que los demás botones;
  usa `buttonClasses`. En Motores, las etiquetas de campo iban a opacidad plena
  (el resto de pantallas las pone al 70 %) y sus textos de ayuda al 50 % (el
  resto, al 60 %). Y el título de Tableros llevaba su frase de entrada pegada
  con un margen negativo en vez de agrupada, como en Motores.

**2026-09-08 · las alternativas del visor (RF-10.2).** Revisar la pantalla
recién hecha destapó cuatro filas más, todas de la misma raíz: el panel lateral
enseñaba las líneas de la posición **anterior** a la que había en el tablero
—que es donde se guardan las alternativas de una jugada—, mientras que las
flechas eran las de la posición en pantalla. Dos posiciones contadas con la
misma forma. Se resolvió anclando el panel a la posición que se ve, la misma que
las flechas:

- Señalar una línea dibuja una continuación que sale de la posición en pantalla,
  no una media jugada por detrás (48), y las evaluaciones de la columna y las de
  las etiquetas de las flechas hablan ya de la misma posición (49).
- "Lo que podías haber jugado en su lugar" se lee desde ahí: el título del panel
  nombra la jugada que se hizo **desde** esta posición cuando salió mal, y la
  lista marca cuál fue con una insignia, en vez de listarla entre sus propias
  alternativas sin distinguirla (50).
- El panel sube al principio del lateral, detrás solo de la precisión, como las
  líneas del motor en el tablero de análisis: detrás de la lista de jugadas
  cambiaba fuera de la pantalla al recorrer la partida (51).

**2026-09-09 · los extractores de patrones (RF-2.8, RF-3.4, RF-3.5, RF-3.2).**
Revisar las dos secciones nuevas del panel de estadísticas y el panel de
momentos críticos del visor dejó abiertas las filas 52 y 53, y tres arreglos
mecánicos sin nada que decidir:

- **C-6.** El panel de momentos críticos enseñaba "72 % → 31 %" con la
  explicación solo en un `title`; ahora la lleva delante, en una línea, como ya
  hacían el panel del motor y la comparación de motores.
- **C-6.** "Al salir", la columna nueva de la tabla de aperturas, decía
  "probabilidad de victoria media" sin decir de quién, cuando es la del usuario
  del panel.
- **C-2.** La columna "De ellos, blunders" se pintaba a opacidad plena en la
  tabla de tipos de error y atenuada en la del reloj, dos tablas seguidas de la
  misma pantalla.

Y las dos filas que sí eran decisiones de presentación, resueltas el mismo día:

- **El punto de vista de la probabilidad de victoria** (52, C-5): el panel de
  momentos críticos la daba desde quien movió, así que tras un error de las
  negras decía 31 % con la barra de evaluación en 69 %, en la misma pantalla y
  a la vez. Ahora la da desde las blancas, como la barra, el gráfico y la
  comparación de motores. La API manda el color de la jugada para poder
  girarla, igual que ya hacía con cada jugada analizada.
- **La regla de cada motivo, escrita** (53, C-6): "Cambió de manos" y "Ocasión
  perdida" solo se explicaban en un `title`. Ahora el panel lleva al pie la
  regla de los motivos que salen en esa partida, como la tabla de tipos de
  error del panel de estadísticas. Solo los que salen: la lista completa sería
  una leyenda de tres líneas que casi nunca aplican todas.

**2026-09-09 · la apertura deducida (RF-3.2).** La tabla ECO propia trajo la
columna ECO de la tabla de aperturas y cambió de dónde salen los nombres. Un
arreglo mecánico del mismo día, sin nada que decidir:

- **C-2.** El vacío de "Por apertura" decía "Importa partidas que empiecen en la
  posición inicial". El concepto ya tiene nombre en la aplicación —"posición
  estándar", y la insignia que lo avisa dice "posición dada"
  (`components/CustomPositionBadge.tsx`)—, y además importar no es lo que
  faltaba: las partidas ya guardadas reciben su apertura en la migración, así
  que las que no aparecen es porque no arrancan en la posición estándar. El
  vacío lo dice ahora con esas palabras.

**2026-09-09 · la insignia "Teoría", que hasta hoy no salía nunca.** La
categoría `book` estaba definida en `lib/classification.ts` desde el principio,
pero no se producía: hasta que existió la tabla ECO, ninguna jugada podía ser
teoría. En cuanto empezó a verse, dos cosas cantaban:

- **Su símbolo era un emoji y los otros siete no** (54, C-2). `📖` se pinta con
  su propia paleta, ignora el color de la insignia, ocupa más alto que el resto
  en una lista donde todas son `text-xs`, y cambia de dibujo según el sistema.
  Ahora es `▤`, monocromo como `★`, `?!` o `??`.
- **"Teoría" no se explicaba en ninguna parte** (55, C-6). Era la única
  categoría cuyo nombre no dice por qué se aplica —y menos con el matiz que
  tiene: una jugada de libro que hunde la posición se clasifica por lo que
  hizo—. Ahora las ocho clasificaciones llevan su regla en
  `lib/classification.ts` y el resumen de jugadas del visor las escribe, que es
  la leyenda de hecho, con la misma forma que la tabla de tipos de error del
  panel de estadísticas.

**2026-09-09 · los filtros de Partidas (RF-5.3).** La barra pasó de cuatro
filtros a nueve y salió de ella `components/FilterBar.tsx`, que es la que usan
ya las dos pantallas que filtran. La revisión dejó abiertas las filas 56 a 60 y
cuatro arreglos mecánicos sin nada que decidir:

- **C-7 · paridad claro/oscuro.** Los filtros de fecha son los primeros
  controles con adorno nativo del navegador (el icono del calendario y su
  desplegable), y sin `color-scheme` el navegador los dibuja siempre claros:
  icono oscuro sobre fondo oscuro. `src/index.css` lo ata al tema, lo que
  arregla de paso las flechas de los campos numéricos de Motores.
- **C-6.** «Desde» y «Hasta» no decían si incluyen el día que se escribe en
  ellos; ahora lo dicen los dos con las mismas palabras, como ya hacía
  «Apertura» con su búsqueda por parte del nombre. Que la ayuda se vea solo al
  pasar el ratón es otra cosa, y es la fila 57.
- **C-3.** El vacío del listado decía «No hay partidas con esos filtros» y
  mandaba a sincronizar aunque no hubiera ningún filtro puesto. Ahora distingue
  los dos casos: sin filtros, la partida que falta es de importarla.
- **C-2.** Un campo deshabilitado se atenuaba pero no cambiaba el cursor, y el
  botón deshabilitado sí (`disabled:cursor-not-allowed` de `buttonClasses`).

**2026-09-09 · la barra de filtros de Partidas (RF-5.3).** Pasar de cuatro
filtros a nueve destapó cinco filas, todas de la misma familia: cosas que la
barra decía a medias o solo con el ratón.

- **El motivo de un filtro deshabilitado, a la vista** (56, C-3/C-7). "Elige un
  jugador primero" vivía en un `title`, que con teclado no aparece nunca —y un
  control deshabilitado ni se tabula—. Ahora la barra lo dice una sola vez, en
  una línea, y explica el porqué: la misma partida es victoria para uno y
  derrota para el otro.
- **Las ayudas de los campos, también** (57, C-6): que Apertura busca por parte
  del nombre y que las fechas incluyen el día escrito. `FieldLabel` las pinta
  bajo el control, como ya hacía la pantalla de motores.
- **Una sola temporización para el mismo filtro** (58, C-2). Estadísticas
  esperaba 400 ms y Partidas consultaba en cada tecla: escribir "sicilian" eran
  ocho peticiones. La espera vive ahora en el campo compartido, así que es la
  misma en las dos pantallas.
- **El listado dice cuántas enseña de cuántas** (59, C-3). Antes solo "Página
  N", y que no hubiera más se descubría cuando "Siguiente" se apagaba. `GET
  /games` devuelve el total en la cabecera `X-Total-Count`, sin envolver la
  lista.
- **Una sola receta de etiqueta de campo** (60, C-2): `components/FieldLabel.tsx`
  reemplaza las dos que convivían —la de la barra de filtros y la `mb-1 block`
  de los formularios de sincronizar, crear tablero y configurar motores—, que
  se veían igual por casualidad.

**2026-09-10 · la comparación de repertorio (RF-3.6).** La primera pantalla que
necesita red mientras se usa (ADR-0010) y la primera cuyo dato puede estar a
medias sin que sea un error. La revisión dejó abiertas las filas 61 a 63 y
cinco arreglos mecánicos sin nada que decidir:

- **C-3 / C-4.** Que la comparación esté incompleta vivía en la misma línea
  gris de `text-xs` que el resumen, y es justo lo que C-3 llama letra pequeña:
  cambia lo que significa la tabla de abajo. Ahora es un `WarningBox`, como las
  limitaciones de la pantalla de Motores, y dice cuántas posiciones faltan y
  por qué hace falta pulsar varias veces.
- **C-2 / C-3.** La consulta no decía qué había conseguido: `fetched` y
  `remaining` llegaban de la API y se tiraban. Ahora terminar deja un
  `SuccessBox` con las dos cifras, como ya hacía sincronizar en Partidas, que
  es la otra acción que sale a internet.
- **C-3.** El vacío tenía un solo título, «Todavía no hay comparación», para
  dos situaciones opuestas: una comparación completa en la que no te sales de
  la teoría contradecía a su propio título. Se distinguen, como ya distingue
  las suyas el listado de Partidas.
- **C-6.** La línea de resumen enseñaba las partidas comparadas solo cuando no
  faltaba ninguna posición, así que el mismo dato aparecía o no según el
  estado; y el aviso hablaba de «salidas del libro», que es jerga que la
  pantalla no explica en ninguna parte. Al pie de la tabla se dice además que
  las jugadas de los maestros van de la más jugada a la menos.
- **C-2.** La columna «Partidas» iba a opacidad plena, y en las otras dos
  tablas del panel el recuento de partidas va atenuado.

Y las tres filas que la revisión de esa misma pantalla dejó abiertas, cerradas
el mismo día:

- **La única acción de la pantalla va en primario** (61, C-2). "Consultar a
  Lichess" era el único botón de Estadísticas y salía secundario, mientras que
  en las otras cuatro pantallas con acción la única de cada una es primaria. Es
  la regla que ya estaba escrita en `components/Button.tsx`.
- **La puntuación va con su marcador** (62, C-2/C-6), como en las otras dos
  tablas del panel: `RecordBadges` sube a `components/`, que es donde debía
  estar desde que lo usan tres tablas.
- **El botón dice qué va a hacer** (63, C-3): cuántas posiciones trae una
  pulsación y cuánto tarda. Los dos números los sabía el servidor y ahora
  viajan en `GET /repertoire`, así que la barra de progreso deja de ser una
  barra sin final.

**2026-09-17 · la importación de un PGN (RF-1.5).** La segunda forma de llenar
el listado de Partidas, junto a la sincronización con chess.com. La revisión
abrió las filas 64 a 67 —la 64 y la 66, cerradas el mismo día, están al final de
esta entrada— y destapó además seis arreglos mecánicos, sin nada que decidir:

- **C-2 · una acción primaria por pantalla.** "Importar" salía primaria al lado
  de "Sincronizar", que también lo era: dos acciones principales en la misma
  cabecera, contra la regla escrita en `components/Button.tsx` y la misma que
  cerró la fila 61. La principal sigue siendo sincronizar.
- **C-2 · "importadas" era el nombre de la otra acción.** El recuadro de éxito
  de sincronizar decía "N partidas importadas en M mes(es)" desde antes de que
  existiera un botón llamado "Importar"; ahora dice "sincronizadas".
- **C-3 · el vacío mandaba a una sola de las dos vías.** "Todavía no hay
  partidas" seguía diciendo solo "Sincroniza tu usuario de chess.com"; nombra
  las dos formas, que es lo que hay arriba.
- **C-3 · el aviso de partidas saltadas sobrevivía a la importación siguiente.**
  Colgaba de `importPgnMutation.data`, que react-query conserva mientras corre la
  petición nueva, mientras que el recuadro verde de al lado sí desaparecía: a
  media importación se veía el amarillo del archivo anterior.
- **C-3 · "Importar" sin archivo no hacía nada ni decía por qué.** El `<input
  type="file">` es `required`, así que lo pide el navegador.
- **C-5 · el hueco tiene una sola forma.** Un PGN manual no dice a qué ritmo se
  jugó y la API lo guarda como `unknown` / `-`, así que el listado y el visor
  enseñaban "Unknown" —en inglés, y un ritmo que no existe— junto a "Blitz" y
  "Rapid", y "-" en la columna de control. Los dos pasan por `lib/format.ts` y
  salen como "—", el mismo hueco del rating que falta y de la precisión sin
  analizar.

Y las dos filas que esa misma revisión abrió y cerró el mismo día, las dos sobre
lo que una importación cuenta de sí misma:

- **La importación dice si reconoció al jugador** (64, C-3). Guardar una partida
  y que no cuente en el dashboard era un desenlace silencioso: el recuadro verde
  decía "N partidas importadas" tanto si "Mi nombre en el PGN" casó con un bando
  como si no casó con ninguno, y la diferencia se descubría días después, al
  echar en falta las partidas en las estadísticas. `PgnImportSummary` trae ahora
  `games_matched_to_player` —en cuántas de las guardadas se reconoció al usuario en
  uno de los dos bandos— y, cuando es cero habiendo guardado algo, la pantalla lo
  dice con un `WarningBox`: las partidas están, pero no cuentan, y el campo que
  hay que revisar tiene nombre.
- **El recuadro verde dice cuántas traía el archivo** (66, C-3/C-6). "3 de 13
  partidas del archivo importadas", en vez de dejar la resta a cargo de quien
  sumara el recuadro verde y el ámbar. El total se compone en el front
  —guardadas más ya presentes más saltadas— y no como campo nuevo de la API: es
  la suma de lo que ya devuelve, y tenerlo dos veces daría dos sitios donde
  descuadrar.

**2026-09-17 · la exportación a PGN anotado (RF-5.5).** El visor gana un
`<a download>` con aspecto de botón en la cabecera. La revisión dejó abiertas
las filas 68 a 70 y dos arreglos mecánicos, sin nada que decidir:

- **C-2 · la fila de acciones de la cabecera no envolvía.** Era `flex
  items-center gap-2` mientras que la del tablero de análisis, con el mismo
  contenido, lleva `flex-wrap`. Con el cuarto control, en una ventana estrecha
  se desbordaba.
- **C-6 · qué lleva el archivo.** "Exportar PGN anotado" no decía qué se
  descarga; lo dice ahora con la misma forma que "Copiar PGN" del tablero de
  análisis, que es la otra acción que saca el PGN de una partida.

**2026-09-18 · las tendencias temporales (RF-3.7).** La sección "Cómo
evolucionas" del panel de estadísticas: una frase de comparación, dos gráficos
y una tabla mes a mes. La revisión abrió las filas 71 a 73 y las tres se
arreglaron en el mismo commit, porque eran defectos de la sección recién
escrita y no deuda heredada:

- **C-3 · un solo mes analizado.** La frase de comparación no se pintaba
  cuando no había con qué comparar, y los dos gráficos se quedaban con un
  punto suelto sin explicar por qué. Ahora el mismo hueco dice "solo hay un mes
  con partidas analizadas: la comparación aparece en cuanto haya un segundo".
- **C-6 · "Rating (—)".** El control de tiempo más jugado podía ser `unknown`
  —el de los PGN importados (RF-1.5), que además no traen rating—, y la leyenda
  nombraba con un hueco una serie vacía. `_most_played_time_class` ya no elige
  `unknown`, y sin control del que hablar el front omite la serie entera: eje,
  línea y la mención del rating en el pie del gráfico.
- **C-6 · orden de las secciones.** Los cuatro tipos de error se estrenaban en
  el gráfico de áreas, dos secciones por encima de la regla que los define.
  "Cómo evolucionas" va ahora detrás de "Por qué fallas", que es donde esa
  regla está escrita.

Y los tres arreglos mecánicos, sin nada que decidir:

- **C-5 · la tasa por cada cien jugadas tiene un solo formateador.** El decimal
  se decidía por separado en tres sitios —las dos columnas de la tabla, el
  tooltip del gráfico de áreas y la frase de `formatTrendSentence`— con un
  `.toFixed(1)` suelto por cada uno. Sale de `formatPerHundredMoves` en
  `lib/format.ts`, que es donde vive el resto del formateo.
- **C-5 · el rating también.** La tabla nueva pasaba por `formatRating` y la de
  "Por control de tiempo", dos secciones más arriba, escribía `?? "—"` a mano:
  el mismo dato con dos reglas en la misma pantalla, y un rating 0 —el de un
  PGN importado— se habría visto como hueco en una y como "0" en la otra.
  `formatRating` acepta ahora el `null` que trae la serie mensual y las dos
  tablas lo usan.
- **C-6 · "Errores / 100" y "Blunders / 100" no decían de qué son cien.** El
  número tampoco se puede comparar con la columna "Errores" en recuento de las
  otras dos tablas del panel. Los dos encabezados llevan su explicación en un
  `abbr`, como ya hacían "V/T/D", "ECO" y "Al salir", y el segundo se llama "De
  ellos, blunders / 100", que es el nombre que esa columna tiene en las otras
  dos tablas.

**2026-09-18 · la partida como tablero y el PGN pegado (RF-6.6, RF-6.7).** El
visor gana "Abrir como tablero" y el tablero de análisis, un panel donde pegar
un PGN. La revisión abrió las filas 74 a 77 y amplió la 69. Las cuatro se
arreglaron en el mismo commit —eran defectos de lo recién escrito, no deuda
heredada— y la 69 queda abierta, porque es una decisión de jerarquía que
afecta también al control de RF-5.5:

- **C-2 · un solo verbo para traer un PGN.** El botón de la cabecera decía
  "Pegar PGN" y el que lo ejecuta "Importar", que es además el nombre que la
  acción tiene en Partidas. Los dos dicen ahora **importar**; que sea el
  reverso de "Copiar PGN" se explica en el texto de ayuda, que es donde cabe.
- **C-3 · una importación a medias se cuenta.** `fromPgn` devuelve
  `truncatedBranches` y el recuadro verde lo dice: "se descartaron N ramas con
  jugadas que no encajan en su posición". Antes cortaba la rama en silencio y
  anunciaba éxito.
- **C-3 · cada fallo dice el suyo.** `fromPgn` ya no devuelve `null` para dos
  cosas distintas: lanza con el motivo, y "la cabecera [FEN …] no describe una
  posición legal" manda a mirar donde está el error y no donde no está.
- **C-2 / C-6 · el título sigue al PGN importado.** Se compone de las
  cabeceras `White`/`Black`/`Date` con `formatBoardTitleFromPgnHeaders`, que
  da el mismo formato que `formatBoardTitleFromGame`. Pesa más aquí que en
  otro sitio porque un tablero **no se puede renombrar** desde ninguna pantalla: el título
  equivocado se quedaba para siempre. Si el PGN no nombra a los dos jugadores
  no se toca, que es mejor que inventar uno.

Y cuatro arreglos mecánicos más, sin nada que decidir:

- **C-3 · importar no tenía desenlace.** "Copiar PGN" deja un `SuccessBox` y su
  reverso no decía nada: el único aviso de que la importación había ido bien
  era que el tablero cambiara solo. Ahora dice cuántas jugadas trae la línea
  principal, como el recuadro verde de la importación de Partidas.
- **C-3 · el desenlace no sobrevive al panel siguiente.** Abrir "Pegar PGN"
  hace `reset()` de la mutación: un recuadro verde de la importación anterior
  junto a un campo vacío se lee como si lo recién pegado ya estuviera dentro.
  Es el mismo fallo que se corrigió en el aviso de partidas saltadas de
  Partidas (RF-1.5).
- **C-3 / C-4 · el aviso de que importar destruye lo que hay** vivía en una
  línea gris de `text-xs` al lado del botón, que es justo lo que C-3 llama
  letra pequeña: cambia lo que va a pasar al pulsar. Es un `WarningBox`, como
  la comparación incompleta del repertorio.
- **C-2 · una acción primaria por pantalla.** "Importar" salía primario con
  "Copiar PGN" también primario tres centímetros más arriba. La misma regla de
  `components/Button.tsx` que cerró las filas 61 y la de Partidas: la principal
  sigue siendo copiar.

Y un quinto, de la pantalla de al lado: **C-6 · "Abrir como tablero" no decía
qué se lleva.** El tablero nace con los comentarios del análisis si está
terminado y con las jugadas peladas si no, y la diferencia se descubría al
llegar; el texto de ayuda la dice, con la misma forma que "Copiar PGN" y
"Exportar PGN anotado".

**2026-09-18 · deshacer, rehacer y el análisis del tablero (RF-6.8, RF-6.9).**
El tablero de análisis gana historial (`Ctrl+Z` / `Ctrl+Y`, con sus dos
botones) y pasa a poder pedir el análisis completo de su línea principal, que
es lo mismo que hace el visor con una partida. La revisión abrió las filas 78
a 82 y las cinco se arreglaron en el mismo commit, y con ellas la **69**, que
llevaba abierta desde RF-5.5: la 82 era su otra mitad y las dos pedían lo
mismo.

- **C-2 · las dos cabeceras con tablero, en el mismo orden.** Queda fijado
  como **girar · historial · motor · las acciones que sacan la partida de
  aquí · la principal**. El visor tenía "Exportar PGN anotado" y "Abrir como
  tablero" delante del motor y ahora van detrás, que es donde el tablero de
  análisis pone "Importar PGN" y "Copiar PGN". Cierra la 69 y la 82.
- **C-2 · el reloj de tiempo transcurrido, en las dos.** `useElapsedSeconds`
  era función local del visor; vive con `useTrackedAnalysis` en `lib/` y
  acompaña también a la barra del tablero. Hace falta ahí igual: con
  posiciones ya cacheadas la barra avanza a saltos y solo el reloj dice
  cuánto se lleva esperado.
- **C-2 / C-5 · la precisión, en el mismo sitio y con la misma forma.** Era
  una línea de texto suelta bajo la cabecera del tablero y es ahora el mismo
  `Panel` "Precisión" que abre el lateral del visor, con "Blancas" y "Negras"
  en lugar de los nombres, porque un tablero de análisis no tiene jugadores.
- **C-3 · el motivo de "Analizar" deshabilitado se enseña.** Estaba solo en
  un `title`, que con teclado no aparece; es la misma solución que cerró la
  fila 56 en la barra de filtros de Partidas.
- **C-3 · un tablero sin analizar lo dice.** Sin esto, las insignias de
  clasificación de RF-6.9 aparecían de la nada la primera vez. El visor ya lo
  resolvía con su `EmptyState` "Sin analizar".

Y siete arreglos mecánicos, sin nada que decidir:

- **C-1 · los atajos nuevos, anunciados donde se anuncian los demás.**
  `Ctrl+Z` y `Ctrl+Y` vivían solo en el `title` de sus botones, que con teclado
  no aparece nunca y que en un botón deshabilitado —que es como están cuando no
  hay historial— tampoco. Van ya en la frase bajo el tablero, junto a «← →
  recorren la línea, Inicio y Fin van a sus extremos», que es donde las dos
  pantallas con tablero anuncian los suyos (`BOARD_HINT_CLASSES`). Chocar no
  chocan: la navegación no mira `ctrlKey` y el historial solo actúa con él.
- **C-2 / C-4 · un análisis que falla es un error en las dos pantallas.** El
  tablero lo decía con `WarningBox` —el recuadro ámbar de «funciona, pero con
  una limitación»— y el visor con `ErrorBox`. Es el mismo estado del mismo
  trabajo: `ErrorBox` en los dos, con el mismo texto de respaldo cuando la API
  no manda motivo.
- **C-5 · el contador de progreso cuenta lo mismo con la misma palabra.** El
  tablero decía «jugada N de M» y el visor «posición N de M» del mismo campo
  `ply`/`total` del mismo evento. Ahora los dos dicen «posición».
- **C-2 · la barra de progreso nombra el motor en las dos.** «Analizando con el
  motor…» del visor no decía con cuál, y el tablero sí. Los dos lo nombran; el
  tablero añade «la línea principal», que es la diferencia real entre los dos
  trabajos.
- **C-2 · «Reanalizar» solo si lo hecho es de ese motor.** El botón del tablero
  miraba solo que hubiera un análisis terminado, así que con uno de Stockfish y
  Lc0 elegido en el desplegable ofrecía «Reanalizar con Lc0», que nunca se
  había hecho. Es la regla que el visor ya aplicaba con `doneAnalysisByEngine`.
- **C-3 · deshacer y rehacer dicen que están trabajando.** La única señal
  mientras la petición viajaba era que los dos botones se apagaran; ahora dicen
  «Deshaciendo…» y «Rehaciendo…», como «Eliminando…» en Tableros o
  «Abriendo…» en el visor.
- **C-3 · un fallo al consultar los análisis anteriores del tablero se ve.**
  `listAnalyses({ boardId })` es lo que decide si el tablero sale como
  analizado; si fallaba, la pantalla quedaba idéntica a la de un tablero que no
  se ha analizado nunca. Lleva ya su `ErrorBox` con reintento, como la consulta
  equivalente del visor.

**2026-09-18 · el editor de posición pieza a pieza (RF-6.1).** La cuarta forma
de empezar un tablero: un panel que se despliega bajo el campo "FEN o PGN" de
Tableros, monta una posición sobre un tablero editable y escribe su FEN en ese
campo. La revisión abrió las filas 83 a 85 y las tres se arreglaron en el
mismo commit:

- **C-1 · el tablero se puede usar con el teclado.** Era la única interacción
  de la aplicación sin esa vía: chessground no pone `tabindex` en ninguna
  casilla ni escucha teclas. Encima del tablero va ahora una rejilla de 64
  botones (`SquareKeyboardGrid`) con una sola parada de tabulador y las
  flechas para moverse dentro, que es el patrón de cualquier rejilla
  accesible; Intro coloca la pieza elegida. La capa entera lleva
  `pointer-events-none`, así que el ratón y el arrastre la atraviesan y
  chessground los sigue recibiendo intactos —comprobado en navegador: clic,
  arrastre desde la paleta y teclado conviven—.
- **C-2 · una sola forma de cerrar el panel.** El botón de arriba decía
  "Cerrar el editor de posición" y dentro había además un "Cancelar": dos
  controles con dos nombres para lo mismo. Ahora el botón de arriba pasa a
  "Cancelar" mientras el panel está abierto, que es lo que ya hace "Importar
  PGN" en el tablero de análisis.
- **C-2 · una sola forma de decir "esto es lo elegido".** La goma se marcaba
  con `variant="primary"`, la variante de la acción principal de la pantalla
  —que aquí es "Usar esta posición"—, mientras las piezas usaban borde y
  fondo índigo. La goma es ahora un botón del mismo tamaño y con la misma
  marca que ellas.

Y seis arreglos mecánicos, sin nada que decidir:

- **C-2 · la caja del panel es la compartida.** El editor escribía a mano
  `space-y-3 p-3` más `PANEL_CLASSES`, que es exactamente lo que da `<Panel>`;
  el panel de "Importar PGN", que es su hermano, usa el componente. La receta
  a mano es de las que se sostienen copiando y pegando (filas 39 a 41).
- **C-1 · la frase bajo el tablero, con la receta de las otras dos.** Era un
  `text-center text-xs opacity-60` escrito a mano, que es literalmente
  `BOARD_HINT_CLASSES`, la constante que usan el visor y el tablero de
  análisis para decir lo mismo en el mismo sitio.
- **C-2 · un solo tamaño de etiqueta de campo.** Los dos `legend` del panel
  ("Qué se coloca", "Enroques disponibles") iban a `text-sm` y las etiquetas de
  `FieldLabel` de al lado ("Mueven", "Captura al paso") al tamaño base: cuatro
  rótulos de la misma clase con dos tamaños, en la misma columna.
- **C-6 · qué hace "Goma", a la vista.** Vivía en un `title`, que con teclado
  no aparece nunca; es la misma corrección que la fila 57 hizo con las ayudas
  de los filtros de Partidas.
- **C-6 · el FEN lleva su etiqueta.** La línea monoespaciada del pie era una
  cadena suelta sin decir qué es, y el editor está justamente para quien no
  tiene un FEN a mano.
- **C-2 · "posición estándar" es el nombre que el concepto ya tiene.** El botón
  decía "Posición inicial" y la insignia `CustomPositionBadge` y el panel de
  estadísticas la llaman "posición estándar" desde la pasada del 2026-09-09.
  El texto de ayuda del campo "FEN o PGN", que decía lo mismo con el otro
  nombre, va con él.

Y un comentario que afirmaba lo contrario de lo que hace el código: el
docstring del editor decía que pulsar las casillas «es lo único que funciona
con el dedo y con teclado» cuando por teclado no funciona nada del tablero
(fila 83). Dice ya lo que hay y a qué fila remite.

**2026-09-18 · la partida propia como formulario (RF-6.5).** Marcar un tablero
dejó de ser una casilla —el tablero no sabe contra quién se jugó, de qué color,
cómo acabó ni qué día— y pasó a ser un panel de cuatro campos
(`features/board/OwnGamePanel.tsx`) que publica el tablero en el historial. La
revisión abrió las filas 86 y 87 y las dos se cerraron en el mismo commit, más
seis arreglos mecánicos de vocabulario:

- **C-1 · el panel es un `<form>` (fila 86).** Los otros cuatro formularios de
  escritura de la aplicación —sincronizar e importar PGN en Partidas, crear
  tablero, configurar motores— se envían con Intro, y este se quedaba mirando:
  quien iba con teclado tenía que llegar hasta el botón. El de guardar es
  `type="submit"`; "Quitar la marca" sigue siendo `type="button"`, que si no
  enviaría el formulario al pulsarlo.
- **C-2 / C-3 · "Quitar la marca" pregunta antes (fila 87).** Saca una partida
  del historial y de las Estadísticas, igual de destructivo que eliminar un
  tablero o una variante, que sí preguntan. La consecuencia —qué partida se va
  y que el tablero se queda entero— se dice en la pregunta y no en un `title`,
  que con teclado no aparece nunca; es la misma razón que cerró las filas 56 y
  57.

Y los seis arreglos de vocabulario:

- **C-2 · los cuatro campos se llaman como sus filtros en Partidas.** Eran
  "Jugué con" y "Contra" para lo que la barra de filtros llama «Color» y
  «Rival», y el resultado se elegía entre "Gané / Tablas / Perdí" donde el
  filtro dice "Victorias / Tablas / Derrotas". Los cuatro rótulos y los tres
  valores usan ya ese vocabulario, en singular porque aquí se habla de una
  sola partida. La primera persona no se usa en ninguna otra pantalla.
- **C-2 · "Estadísticas" es como se llama la pantalla.** La línea de estado
  decía "cuenta en el dashboard" y la insignia del listado "cuenta en tus
  estadísticas": dos nombres, ninguno el de la barra de navegación. Y "los
  patrones", que salía en las dos frases, no es nombre de nada que el usuario
  vea: las secciones de esa pantalla se llaman "Por qué fallas" o "Cómo
  evolucionas".
- **C-2 · el mismo texto no puede ser dos acciones.** "Marcar como partida
  propia" era a la vez el botón que abre el panel y el que lo envía. El que
  envía se llama "Guardar los datos" marque por primera vez o corrija, que es
  la misma forma que "Importar PGN" (abre) e "Importar" (ejecuta).
- **C-2 · ir a una partida se llama "Ver partida".** El enlace de la línea de
  estado decía "Ver en el historial" y se veía como texto suelto, mientras que
  las dos pantallas que llevan a una partida usan un enlace con aspecto de
  botón (`buttonClasses`) y ese nombre. La misma corrección que cerró la fila
  de "Ver tablero" en el barrido del 2026-09-08.
- **C-5 · el hueco del control de tiempo se nombra como se ve.** El aviso
  prometía que la partida saldría "bajo el control de tiempo «sin
  determinar»", pero lo que la pantalla enseña para `unknown` es "—"
  (`formatTimeClass`), el mismo hueco del rating y de la precisión.
- **C-3 · el pie del panel "Precisión" decía lo contrario de lo que hace el
  sistema.** Afirmaba que el análisis del tablero "no cuenta en tus
  estadísticas" siempre, y desde RF-6.5 sí cuenta cuando el tablero está
  publicado y lo analizado sigue siendo la línea principal
  (`services/own_games.py::link_analyses_to_own_game`). Ahora dice una cosa u otra según
  el tablero.

Y una fuga de vocabulario interno: dos textos de usuario llevaban el
identificador del requerimiento dentro —"Cuenta en tus estadísticas (RF-6.5)"
en la insignia del listado y la misma coletilla en el pie de "Precisión"—. Los
RF viven en `docs/02-requerimientos.md`, no en la pantalla.

**2026-09-19 · las cuatro que quedaban, al recorrer el apéndice de la fase 2.**
Las heredadas de la importación de PGN (RF-1.5) y de la exportación a PGN
anotado (RF-5.5), que llevaban abiertas desde el 2026-09-17:

- **Fila 65 (C-2) · la cabecera de Partidas deja de repartir tres cosas en una
  fila.** El título va en su propia línea y los dos formularios en la de abajo,
  alineados por su base. Con `justify-between` y tres hijos, al envolverse en
  una ventana estrecha el título se quedaba solo arriba y las dos formas de
  traer partidas acababan a distinta altura, cuando son lo mismo y se leen
  juntas.
- **Fila 67 (C-6) · el listado dice de dónde vino cada partida.** `GameSummary`
  expone ya `platform`, y `components/GameSourceBadge.tsx` marca lo que se sale
  de la norma: "PGN importado" (RF-1.5) y "tablero propio" (RF-6.5), con el
  motivo del hueco en el `title`. Las de chess.com no llevan insignia, que son
  la inmensa mayoría y marcarlas todas sería ruido. Misma insignia y mismo orden
  en el listado y en la cabecera del visor, junto a `CustomPositionBadge`, con
  la que convive: un PGN importado puede además empezar en una posición dada.
- **Fila 68 (C-3) · "Exportar PGN anotado" existe siempre**, deshabilitado y
  diciendo qué falta cuando no hay análisis terminado. Antes no aparecía hasta
  que lo había, así que quien abría una partida sin analizar no podía saber que
  la exportación existe ni que analizar es lo que la trae. Es lo que ya hacía la
  barra de filtros con sus tres campos (fila 56).
- **Fila 70 (C-3) · la descarga tiene desenlace en pantalla.** Dejó de ser un
  `<a download>` apuntando a la API —donde un 409 o un 404 se guardaban como si
  fueran el archivo, en silencio— y pasa por `api.getAnalysisPgn`, que comprueba
  la respuesta y solo entonces guarda (`lib/download.ts`), respetando el nombre
  que propone el servidor en su `Content-Disposition`. El error sale en el mismo
  `ErrorBox` que el resto de acciones del visor.

**2026-09-19 · la capa de ocupación del tablero (RF-7.1 a RF-7.7).** La primera
capa que se dibuja **encima** del tablero en las dos pantallas que lo tienen, con
su panel de control y su leyenda. La revisión abrió las filas 88 a 90 —las tres
cerradas el mismo día— y dejó nueve arreglos mecánicos más, sin nada que
decidir:

- **C-1 · las flechas de la rejilla de casillas no mueven además la partida.**
  `SquareKeyboardGrid` nació en el editor de posición, donde nadie más escucha
  el teclado; en el visor y en el tablero de análisis escucha
  `useMoveNavigationKeys` en `window`, así que con el foco en una casilla una
  flecha movía el foco **y** la partida a la jugada siguiente —que además
  descarta la casilla elegida—. La rejilla para la pulsación antes de que suba
  a la ventana. Es el mismo choque que ya se corrigió con el desplegable de
  motor en el barrido del 2026-09-08.
- **C-2 · encender y apagar se dice con los mismos dos verbos.** El botón del
  panel decía "Activar" / "Desactivar" mientras el único otro interruptor de la
  aplicación —el del motor, en la cabecera de la misma pantalla— dice "Encender
  motor" / "Apagar motor", y el propio panel escribía "se enciende" dos líneas
  más abajo. Con el rótulo diciendo ya en qué estado está, el `aria-pressed`
  sobraba: se queda como está en la paleta del editor, donde el rótulo no
  cambia.
- **C-1 · el atajo se anuncia entero.** La frase bajo el tablero decía "Con O se
  enciende la capa de ocupación" y la tecla también la apaga, que es lo que hay
  que saber para deshacer el descubrimiento.
- **C-3 / C-4 · encendida y sin posición legible no es lo mismo que apagada.**
  `computeOccupancy` devuelve `null` cuando no puede leer el FEN, y el panel
  caía en la misma rama que estando apagado: enseñaba "se enciende aquí o con la
  tecla O" con el botón puesto en "Apagar". Es un `ErrorBox`, como el resto de
  fallos de las dos pantallas.
- **C-6 · la leyenda solo explica lo que está en pantalla.** La fila de la pieza
  colgada se pintaba siempre, también con "Piezas colgadas" desmarcado, mientras
  que la del rayo X ya era condicional: la leyenda nombraba un borde rojo que no
  estaba en ninguna casilla.
- **C-7 · paridad claro/oscuro.** Dos bordes se quedaron con el color por
  defecto de Tailwind, que es el mismo gris claro en los dos temas: el de la
  tecla `<kbd>` —el primero de la aplicación— y el de la muestra "sin control" de
  la leyenda. Llevan ya el par `slate-300` / `dark:slate-700` del resto de
  bordes.
- **C-2 · los dos separadores del mismo panel, del mismo color.** Uno iba a
  `slate-100` y el otro a `slate-200`, que es el de la cabecera de `Panel`.
- **C-5 / C-2 · el editor de posición y la capa nombran las piezas con la misma
  tabla.** `PIECE_KINDS`, que vivía en `PositionEditor`, es ya
  `components/board/pieces.ts`, de donde salen también los nombres del panel de
  ocupación; y la rejilla enfocable dejó de estar copiada dentro del editor
  para ser `components/board/SquareKeyboardGrid.tsx`, que usan las dos capas.
- **El único valor fuera de la escala, justificado por escrito.** El número de
  atacantes que se pinta en cada casilla va en `text-[0.55rem]`: una casilla
  mide un octavo del tablero y `text-xs`, el escalón más pequeño de la escala,
  taparía la pieza que hay debajo. Queda dicho en el código, que es donde se va
  a leer.

Y las tres filas que sí había que decidir:

- **Fila 88 · las tres marcas se apagan igual (C-2).** "Qué se marca" apagaba
  las piezas colgadas y los rayos X, pero el borde a rayas de las clavadas
  estaba siempre. Ahora son tres casillas y un solo estado, `marks`, en vez de
  dos banderas sueltas y una marca fija: tres cosas de la misma clase no pueden
  comportarse de dos maneras en el mismo panel.
- **Fila 89 · cada marca dice qué va a salir antes de encenderla (C-6).**
  "Rayos X" y "Piezas colgadas" son los rótulos más técnicos de la pantalla y su
  única explicación estaba en la leyenda, que solo aparece cuando la marca ya
  está encendida. Las tres llevan su frase de ayuda bajo la casilla, como los
  filtros de Partidas desde la fila 57.
- **Fila 90 · el panel se queda bajo el tablero, y aquí queda escrito por qué
  (C-2).** Los demás paneles de esas dos pantallas viven en el lateral, pero
  ninguno de ellos es la leyenda de algo que se esté pintando en el tablero:
  este lo es, y leer "borde a rayas ámbar" a dos columnas de distancia de la
  casilla que lo lleva obliga a cruzar la vista en cada consulta. Está en el
  mismo sitio en las dos pantallas, que es lo que C-2 pide de verdad; la
  jerarquía "contenido a la izquierda, paneles a la derecha" cede ante la
  proximidad cuando el panel explica un dibujo.

**Y un nombre que se revisó y se deja como está.** Que la acción se llame
"Exportar PGN anotado" y no "Exportar PGN", teniendo Partidas un "Importar
PGN", no es asimetría gratuita: lo que sale no es el PGN que entró, sino el
PGN con los comentarios del análisis y sus variantes, y "Copiar PGN" del
tablero de análisis ya usa el nombre corto para lo otro. Tres verbos distintos
—importar, copiar, exportar— para tres acciones distintas cumplen C-2.

**Decidido el 2026-09-07, no es incoherencia.** Dos cosas que este inventario
llegó a listar y el autor resolvió por criterio, no por descuido:

- **La precisión se enseña con `%`** ("87.3 %") aunque no sea una proporción,
  sino el índice 0-100 de Lichess. Es la convención del dominio —Lichess y
  chess.com la muestran así— y es de donde viene el usuario de LUCIA.
- **Los controles de tiempo se quedan en inglés** ("Bullet", "Blitz", "Rapid",
  "Daily"). "Blitz" y "bullet" son préstamos de uso corriente en el ajedrez en
  español; traducir unos sí y otros no dejaba cuatro formas gramaticales
  distintas en la misma columna, y son los términos que el usuario ya ve en
  chess.com.

**El visor ya dibuja las mismas flechas que el tablero de análisis.** Llegó a
tener una sola, y no era incoherencia sino falta de dato: el análisis guardado
solo persistía `best_move_uci` por jugada. Desde RF-10 (2026-09-08) guarda
todas las líneas, y las dos pantallas usan `arrowsFromEngineLines` y la misma
lista de líneas (`components/board/EngineLineList.tsx`). Un análisis viejo cuyas
posiciones ya no estén en `position_cache` se queda con su única flecha: es lo
que hay guardado, no una forma distinta de enseñarlo, y el visor lo dice con un
`EmptyState` en el lateral en vez de dejar el hueco. Lo que esa misma pasada
dejó abierto son las filas 48 a 51 del inventario.

**Los números no se localizan a propósito.** `formatDate` usa el locale `es`,
pero los decimales van con punto (`+1.25`, `54.3 %`) porque la notación de
evaluación en ajedrez lo usa en todas partes; poner coma en los porcentajes y
punto en las evaluaciones sería peor que el punto en los dos.

## Cómo se verifica

Antes de comitear cualquier cambio que toque `apps/web`:

1. Recorrer los siete criterios contra las pantallas afectadas.
2. Si el cambio introduce una acción, un estado o un dato del motor que ya
   existe en otra pantalla, comprobar que se llama, se coloca y se formatea
   igual — o cambiar las dos a la vez.
3. Si aparece una incoherencia que no se arregla en el mismo commit, añadirla
   al inventario de arriba —`# · Incoherencia · Dónde · Criterio`, numerando
   desde el 91— en vez de dejarla suelta. Una fila se borra cuando se arregla,
   y las demás no se renumeran: el número es la referencia con la que se habla
   de ella en un commit o en una revisión.
