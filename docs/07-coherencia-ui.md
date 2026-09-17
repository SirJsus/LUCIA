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
filas 61 a 63, que siguen abiertas: son las únicas. El inventario vacío es como
debería encontrarse siempre que se lea este documento.

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

## Inventario de incoherencias: vacío (al 2026-09-10)

**No queda ninguna abierta.** El inventario llegó a tener 63 filas y están todas
cerradas. El rastro de qué se hizo está más abajo.

## Lo que se cerró

Las 63 filas que llegó a tener este inventario se cerraron en nueve pasadas, y
aquí queda el rastro de qué se hizo, para que un `git blame` no sea la única
forma de averiguarlo.

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
   desde el 64— en vez de dejarla suelta. Una fila se borra cuando se arregla,
   y las demás no se renumeran: el número es la referencia con la que se habla
   de ella en un commit o en una revisión.
