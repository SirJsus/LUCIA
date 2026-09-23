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
debería encontrarse este documento siempre que se lea, y ese día lo estuvo por
primera vez: no es un estado alcanzado, sino el estado del que se parte la
próxima vez. La próxima vez fue el mismo 2026-09-19, con la pantalla de
Entrenamiento (RF-4.1, con RF-10.3), que abrió las filas **91 a 93** y dejó
seis arreglos en el mismo commit. El sparring contra el motor (RF-4.3), del
2026-09-21, le añadió dos pantallas a esa misma sección y estrenó la primera
sub-navegación de la aplicación: abrió las filas **94 a 96**, amplió la 91 al
tablero donde se juega y dejó ocho arreglos en el mismo commit. El drill de
aperturas (RF-4.2), del mismo día, es la tercera pestaña de Entrenamiento y la
pantalla gemela de la de puzzles: abrió las filas **97 a 100** —todas de lo
que separa a las dos gemelas—, amplió otra vez la 91 y dejó tres arreglos en el
mismo commit. Re-jugar desde el error (RF-4.4), del mismo día, es la cuarta
pestaña y la primera acción de Entrenamiento que se ofrece también desde fuera
de la sección —desde el visor de una partida propia—: abrió las filas **101 a
103**, amplió la 92 a la pantalla nueva y la 95 al cuarto listado, y dejó ocho
arreglos en el mismo commit. El plan de entrenamiento semanal (RF-4.5), del
mismo día, cierra **RF-4 entero** —no la fase 3, a la que le queda la capa de
ocupación en las pantallas de entrenamiento— y **cambia la portada de la
sección**: entrar en
Entrenamiento ya no lleva a los puzzles sino al plan, que es la pantalla que
dice por dónde empezar, y los puzzles se mudan a `/training/puzzles`. Abrió las
filas **104 a 106** —las tres sobre las palabras con las que el plan cuenta lo
que falla, de las cuales la 106 se cerró el mismo día— y dejó ocho arreglos en
el commit, uno de ellos el primitivo `ProgressBar` que ahora comparten el
recuadro de progreso y las tarjetas de deberes. La capa de ocupación en las
pantallas de entrenamiento (RF-7.1 a RF-7.7 sobre RF-4.1, RF-4.2 y RF-4.3), del
2026-09-22, cierra la fase 3 y deja por primera vez **cinco pantallas con el
mismo tablero y la misma columna**: tablero, frase de atajos y panel de
ocupación, en ese orden. Comparar las cinco de una vez es lo que abrió las
filas **107 y 108** —la 108, cerrada el mismo día— y lo que precisó la 91; la
divergencia deliberada —las tres
marcas arrancan apagadas en entrenamiento y encendidas en el visor y en el
tablero de análisis— se resolvió dentro del mismo commit, diciéndolo en el
panel donde se ven apagadas. Y el **barrido de cierre de la fase 3**, del mismo
2026-09-22, recorre las quince que quedaban abiertas y las cierra todas: es lo
que se decidió el 2026-09-19 al abrir la primera de ellas, esperar a tener las
seis pantallas delante para decidir de una vez en qué se parecen. Comprobar ese
barrido —leer las cinco pantallas con tablero estado por estado— dejó cinco
arreglos más y destapó la **109**, que se cerró en el mismo commit: dar a la
partida de sparring cabecera de pantalla de detalle (fila 94) es lo que la puso
a compararse con el visor también por dónde tiene sus acciones. El inventario
queda vacío.

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
| C-5 | **Un dato, una forma.** La evaluación, la clasificación de jugada y el nombre del motor se presentan igual en todas partes: mismo signo, misma unidad, mismo punto de vista (blancas) y mismo formateador (`lib/score.ts`). **Excepción, decidida el 2026-09-22 al cerrar la fila 92**: una frase puede contarlo desde el bando de quien entrena si lo nombra explícitamente («Tu probabilidad de victoria pasó de…»). Es lo que hacen el puzzle resuelto (RF-4.1) y la lista de re-jugar (RF-4.4), donde lo que se cuenta es el error propio: desde las blancas, quien juega con negras leería «31 puntos más» delante de su propia equivocación. El punto de vista de las blancas sigue siendo obligatorio en todo número suelto —una columna, una insignia, un gráfico—, que es donde nadie puede preguntar desde dónde se cuenta. |
| C-6 | **Legible sin saber de ajedrez.** Todo número del motor va acompañado de etiqueta, leyenda o representación visual. `+0.35` solo, sin más, no comunica nada a quien no lee evaluaciones. |
| C-7 | **Accesibilidad mínima.** Foco visible, `aria-label` en los botones que son solo icono, y ningún significado transmitido únicamente por color. |

## Inventario de incoherencias abiertas (al 2026-09-23)

**Ninguna.** El barrido de cierre de la fase 3 recorrió las quince que quedaban
—las dos de la pantalla de puzzles (91 y 92), las tres que abrió el sparring
(94 a 96), las cuatro del drill de aperturas (97 a 100), las tres de re-jugar
desde el error (101 a 103), las dos del plan semanal (104 y 105) y la que
destapó llevar la capa de ocupación a las tres pantallas de entrenamiento
(107)— y las cerró todas. Comprobarlo a continuación dejó cinco arreglos más y
destapó una fila nueva, la **109**, consecuencia directa de cerrar la 94: dar
a la partida de sparring cabecera de pantalla de detalle la puso a compararse
con el visor y con el tablero de análisis también por dónde tiene sus acciones.
Se cerró en el mismo commit subiéndolas a la cabecera. El detalle de las
dieciséis está abajo, en la entrada del 2026-09-22.

Es la segunda vez que queda vacío. La primera fue
el 2026-09-19, al cerrar las cuatro heredadas de la fase 2 —la 65 y la 67 de la pantalla de Partidas y la 68
y la 70 del control de exportar del visor—, y volvió a llenarse ese mismo día
con la pantalla de Entrenamiento: era la primera sección que se construía
entera de una vez, y compararla consigo misma y con lo que ya había daba más de
lo que cabía en un commit. Por eso se decidió entonces dejarlas para el final
de la fase, cuando estuvieran las seis pantallas y se pudiera decidir de una
vez cómo se parecen; esto es ese momento.

Los números no se renumeran al cerrar una fila, que es la referencia con la que
se habla de ella en un commit: la 93 y la 106 están cerradas y sus números no
se reutilizan. La siguiente fila que se abra será la **110**.

## Lo que se cerró

Las 109 filas de este inventario, todas cerradas, se cerraron en trece pasadas,
y aquí queda el rastro de qué se hizo, para que un `git blame` no sea la única
forma de averiguarlo. Las seis pasadas que construyeron Entrenamiento —la de la
pantalla de puzzles, la del sparring, la del drill de aperturas, la de re-jugar
desde el error, la del plan semanal y la de la capa de ocupación— están al
final: esas no cerraron filas, las abrieron. La decimotercera, el barrido de
cierre de la fase 3, es la que las cerró todas, y va la última de todas.

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

**2026-09-19 · la pantalla de Entrenamiento (RF-4.1, con RF-10.3).** La
primera entrada nueva de la barra de navegación desde que existe este
documento, y la primera cuyo tablero se usa para **responder** y no para
recorrer ni para montar una posición. La revisión abrió las filas 91 a 93 —las
tres siguen abiertas, y están arriba— y dejó seis arreglos en el mismo
commit, sin nada que decidir:

- **C-2 · rendirse es una acción, no dos.** "Ver la solución" estaba dos veces
  —suelta antes de responder y dentro del recuadro de aviso tras fallar—, con
  dos tamaños (`md` y `sm`) y en dos sitios, así que fallar movía de posición un
  botón que hace exactamente lo mismo. Es una sola, en `md`, en el mismo lugar
  del lateral mientras el puzzle esté abierto; el aviso se queda con "Volver a
  intentarlo", que es lo único que solo tiene sentido después de fallar.
- **C-2 · una acción primaria por pantalla.** "Generar puzzles" salía primaria y
  al mismo tiempo lo eran "Volver a intentarlo" y "Siguiente puzzle" del puzzle
  de debajo: hasta tres primarias a la vez. La principal de esta pantalla es
  resolver, así que generar baja a secundaria. Es la regla de
  `components/Button.tsx` que ya cerró la fila 61.
- **C-2 · ir a una partida se llama "Ver partida".** El enlace del resultado
  decía "Ver la partida", y las otras dos pantallas que llevan a una usan ese
  nombre desde el barrido del 2026-09-08.
- **C-6 · qué hace "Generar puzzles", a la vista.** Vivía en un `title`, que con
  teclado no aparece nunca; va bajo el botón, como las ayudas de los filtros de
  Partidas desde la fila 57.
- **C-6 / C-7 · las flechas del puzzle resuelto llevan leyenda.** La verde es la
  jugada que hacía falta y la roja la que se jugó en la partida, y la diferencia
  estaba solo en el color. La frase bajo el tablero —la misma que anuncia los
  atajos en las otras pantallas (`BOARD_HINT_CLASSES`)— la dice al cerrarse el
  puzzle, y nombra solo los colores que están dibujados, como la leyenda de la
  capa de ocupación.
- **C-6 · el contador de intentos contaba uno de más.** Tras fallar el primero,
  el aviso decía "Llevas 2 intentos": `attempt` es el intento que viene, no los
  hechos. Y con uno solo escribía "1 intentos".

Y dos rupturas deliberadas del patrón, que se revisaron y se dejan como están:

- **El tablero del puzzle no tiene barra de evaluación**, al contrario que el
  visor y el tablero de análisis. No es descuido: la evaluación de la posición
  es media respuesta. Los números salen al cerrar el puzzle, dentro del panel
  "Lo que pasó en la partida". El editor de posición ya era un tablero sin barra
  por una razón parecida (ahí no hay nada que evaluar).
- **Ni la solución ni la jugada de la partida llegan al navegador** mientras el
  puzzle está abierto: `PuzzleAnswerOut` manda `solutions_san` vacío y
  `played_san` a `null` hasta que se cierra. Es lo que permite además aceptar
  cualquier jugada equivalente (RF-10.3) sin que el cliente sepa cuáles son. Lo
  que sí viaja abierto el puzzle son `win_percent_before` / `win_percent_after`
  y `classification`, que no se enseñan hasta cerrarlo pero se pueden leer en la
  respuesta; si esa rendija importa, es del lado de la API y no de esta
  pantalla.

**2026-09-21 · el sparring contra el motor (RF-4.3).** Dos pantallas más en la
sección de Entrenamiento —la antesala, con el formulario de rival y fuerza y el
listado de partidas, y la partida en curso— y el primer tablero de la
aplicación donde se **juega**. La revisión abrió las filas 94 a 96, amplió la
91 al tablero del sparring y dejó ocho arreglos en el mismo commit, sin nada
que decidir:

- **C-1 · el formulario se envía con Intro.** "Nueva partida" era un `<div>`
  con un botón `onClick`, así que quien iba con teclado tenía que llegar hasta
  el botón mientras que los otros cinco formularios de escritura de la
  aplicación —sincronizar e importar PGN, crear tablero, partida propia,
  configurar motores— se envían desde cualquier campo. Es la misma corrección
  que cerró la fila 86.
- **C-2 · la receta del enlace de navegación deja de estar copiada.** La
  sub-navegación de Entrenamiento repetía carácter a carácter el `className`
  del enlace no marcado de la barra principal. Es `NAV_LINK_CLASSES` en
  `components/styles.ts`, de donde sale también el de `Layout`: la familia de
  las filas 39 a 41, coherencia que se sostenía copiando y pegando.
- **C-2 · abandonar pregunta antes.** Termina la partida como derrota y no hay
  deshacer, igual de destructivo que eliminar un tablero, borrar una variante o
  quitar la marca de partida propia, que sí preguntan (fila 87). La
  consecuencia se dice en la pregunta.
- **C-2 · el enlace de la fila del listado, del tamaño de los otros dos.** Iba
  en `md`, que es el tamaño de una acción de cabecera; "Ver partida" en
  Partidas y "Ver tablero" en Tableros van en `sm` desde el barrido del
  2026-09-08.
- **C-4 · la lista de jugadas vacía es un `EmptyState`.** Era un `<p>` con la
  frase "Todavía no se ha jugado nada", que es justo la frase suelta que el
  criterio prohíbe. Va con el mismo envoltorio `p-3` que el vacío "Sin
  alternativas guardadas" del lateral del visor.
- **C-5 · el número de jugada sale de `lib/moves.ts`.** `turnsOf` lo calculaba
  con `index / 2 + 1`; es `moveNumberOf`, el mismo de las otras cinco pantallas
  que numeran. Una partida de sparring siempre arranca en la posición estándar,
  así que hoy daba lo mismo: lo que se evita es la sexta regla de numeración.
- **C-6 · "Abrir como tablero" dice qué se lleva**, con la misma forma que el
  del visor, que lo ganó en la revisión de RF-6.6: sin eso, la diferencia entre
  lo que queda aquí y lo que se va al tablero se descubre al llegar.
- **C-7 · el deslizador de fuerza no se llama de dos maneras.** Llevaba
  `aria-label="Fuerza del motor en Elo"` dentro de un `FieldLabel` que ya lo
  envuelve y lo nombra "Fuerza: 1500 Elo": el nombre accesible tapaba al
  visible sin contenerlo, que es lo que rompe el manejo por voz. Ningún otro
  control dentro de `FieldLabel` lleva `aria-label`, porque la etiqueta ya lo
  nombra.

**El patrón nuevo: la sub-navegación de sección.** Entrenamiento es la primera
sección con varias pantallas hermanas —Puzzles y Sparring, y le faltan el drill
de aperturas (RF-4.2) y el plan semanal (RF-4.5)—, así que la elección vive
dentro de la sección, bajo el título, y no en la barra principal, que si no
crecería una entrada por cada forma de entrenar. Las pestañas se ven como los
enlaces de la barra principal y marcan el activo igual, para que "dónde estoy"
se lea lo mismo en los dos niveles. La siguiente sección que necesite
sub-navegación sale de `features/training/TrainingHeader.tsx`. Lo que este
patrón todavía no resuelve es cómo se encabeza la pantalla de detalle que
cuelga de una de esas pestañas, y eso es la fila 94.

Y tres rupturas deliberadas más, revisadas y dejadas como están:

- **El tablero del sparring no tiene barra de evaluación**, por lo mismo que el
  de los puzzles: una barra diciendo a cada jugada quién va ganando convierte
  la partida en un análisis asistido. Para eso está "Abrir como tablero" cuando
  la partida termina.
- **El tablero no se puede girar.** Las dos pantallas que tienen "Girar
  tablero" son de análisis, donde no hay bando propio; aquí se juega con un
  color y mirar desde el otro lado no es una vista, es otra partida.
- **"Abrir como tablero" sale en primario aquí y en secundario en el visor.**
  En el visor la acción principal de la pantalla es analizar; en una partida de
  sparring terminada esta es la única que queda, y la única acción de una
  pantalla va en primario (fila 61).

**2026-09-21 · el drill de aperturas (RF-4.2).** La tercera pestaña de
Entrenamiento: una pantalla con el ciclo de la de puzzles —generar, la cola del
día, recorrer una— y un tablero donde se repite jugando la línea. Se escribió a
propósito como gemela de la de puzzles, así que la revisión fue comparar las
dos: abrió las filas **97 a 100**, todas de sitios donde el parecido se rompe,
amplió la **91** al tercer tablero donde se mueve una pieza y dejó tres
arreglos en el mismo commit, sin nada que decidir:

- **C-5 · la puntuación de la apertura pasa por `formatPercent`.** Se componía
  a mano con `Math.round(...) + " %"`, así que el mismo número salía entero en
  el drill y con un decimal en las cuatro tablas que ya lo enseñan —la de
  salidas del repertorio incluida, que es justo de donde vienen la mitad de los
  drills—. Es la familia de arreglos de la fila 52 y del `.toFixed(1)` suelto
  de las tendencias.
- **C-5 · el número de jugada sale de `lib/moves.ts`.** `playerMoveNumber` lo
  calculaba con `(ply - first_ply) / 2 + 1`: la séptima regla de numeración de
  la aplicación. Es `moveNumberOf`, y da lo mismo porque una línea de apertura
  arranca en la posición estándar. El mismo arreglo que se hizo el mismo día en
  la lista de jugadas del sparring, y por la misma razón: lo que se evita es
  otra regla, no un número equivocado.
- **C-3 · un comentario que afirmaba lo contrario de lo que hace el código.**
  Decía que la foto incompleta de la teoría "se dice siempre que lo esté, y no
  solo al generar" cuando el aviso cuelga de `generateMutation.data` y solo
  aparece tras pulsar el botón. Dice ya lo que hay y remite a la fila 99, que
  es lo que haría falta para que fuera verdad.

Y cuatro rupturas del patrón que se revisaron y se dejan como están:

- **El tablero del drill no tiene barra de evaluación**, por lo mismo que el
  del puzzle y el del sparring: lo que se entrena es recordar la línea, y una
  evaluación en pantalla dice si la jugada que se acaba de hacer era la buena.
  Razonado en `apps/web/src/features/training/README.md`.
- **Fallar no enseña la jugada de la línea y rendirse sí.** Es el mismo trato
  que da el puzzle con "Ver la solución", y el botón se llama igual de largo
  ("Ver la línea"), va en el mismo sitio —debajo del aviso de fallo, mientras
  el drill esté abierto—, en secundario y con la misma etiqueta "Comprobando…"
  mientras la petición viaja.
- **La pestaña se llama "Aperturas" y sus hermanas "Puzzles" y "Sparring".**
  Las tres nombran lo que se entrena y no cómo, que es lo que hace falta para
  elegir; "Aperturas" es además el nombre que el concepto ya tiene en
  Estadísticas ("Por apertura").
- **La cola mezcla las dos barajas** —las líneas donde te sales de la teoría
  (RF-3.6) y las aperturas que rinden mal (RF-3.2)— ordenadas por cuándo tocan
  y no por su origen, que se dice con una insignia. Separarlas obligaría a
  elegir por cuál empezar cada día, y para quien entrena son lo mismo.

**2026-09-21 · re-jugar desde el error (RF-4.4).** La cuarta pestaña de
Entrenamiento —una lista de los errores propios más caros— y la primera acción
de la sección que se ofrece además desde fuera de ella: el visor de una partida
propia gana "Jugar desde aquí" junto a "Abrir como tablero". Lo que se retoma es
una partida de sparring desde otra posición, así que se juega en la pantalla de
RF-4.3 y el formulario de dificultad, que antes vivía dentro de `SparringPage`,
es ya un componente que usan las tres pantallas que abren una partida
(`features/training/SparringSetupForm.tsx`): esa extracción es la mitad del
trabajo de coherencia de este cambio y se hizo antes de la revisión. Abrió las
filas **101 a 103**, amplió la **92** —la lista repite el punto de vista del
puzzle— y la **95** —el cuarto listado copia la receta de fila del tercero—, y
dejó ocho arreglos en el mismo commit, sin nada que decidir. La **98** no se
mueve: re-jugar no añade un cuarto tablero ni un cuarto panel lateral, lleva al
del sparring, que sigue encabezándose como estaba.

Los arreglos:

- **C-5 · lo que costó el error se dice con una sola frase.** "Tu probabilidad
  de victoria pasó de 72.0 % a 31.0 %: 41 pts de prob. de victoria menos"
  estaba escrita dos veces, con su resta incluida, en el puzzle resuelto y en
  la lista de re-jugar: dos sitios donde el mismo dato podía acabar diciéndose
  de dos maneras. Sale de `formatOwnWinPercentLossSentence` en `lib/format.ts`,
  que es donde vive el formateo y donde ya vivía `formatTrendSentence`. De paso
  deja la fila 92 en un solo sitio: girar el punto de vista será un cambio y no
  dos.
- **C-5 · el número de jugada sale del FEN y no del `ply`.** La lista numeraba
  con `moveNumberLabel(position.ply)`, que es relativo al inicio de la partida,
  así que un error de la jugada 15 de una partida importada que empieza en la
  12 salía como la 4. Es `plyFromFen(position.fen)`, exactamente lo que ya hace
  el puzzle con la suya.
- **C-2 · la acción se llama igual en las dos pantallas desde las que se
  hace.** El botón que despliega el formulario decía "Re-jugar desde aquí" en
  la lista y "Jugar desde aquí" en el visor; es "Jugar desde aquí" en los dos,
  que es el nombre que funciona también donde no hubo ningún error que
  rehacer.
- **C-2 · y el botón que la ejecuta, también.** Decía "Retomar la partida" en
  la lista y "Empezar partida" en el visor, en el mismo formulario. Los dos
  dicen **retomar**; "Empezar partida" se queda en Sparring, que es la otra
  cosa: una partida desde cero.
- **C-2 · el control de la fila va en `sm`.** Iba en `md`, que es el tamaño de
  una acción de cabecera, al lado de un "Ver partida" en `sm`: dos botones
  contiguos de dos tamaños en la misma fila. Es el mismo arreglo que se hizo el
  mismo día en la fila del listado de sparring.
- **C-2 · el panel se llama "Tus errores".** Se llamaba "Tus peores momentos",
  y "momento" ya nombra otra cosa en la aplicación —los momentos críticos del
  visor (RF-2.8), que se eligen con otra regla—, mientras que esta pantalla
  llama errores a lo que enseña en su frase de entrada y en su vacío. "Tus …"
  es además como se titula el listado de la pestaña de al lado.
- **C-3 · el fallo al retomar sale donde se pulsó.** El `ErrorBox` colgaba de
  la cabecera de la pantalla, así que elegir el error decimoquinto y que
  fallara dejaba el aviso fuera de la pantalla. Va bajo el formulario del error
  elegido, y elegir otro hace `reset()`: un recuadro rojo sobre un formulario
  recién abierto se lee como si acabara de fallar ese (es lo mismo que se
  corrigió al abrir "Importar PGN" en el tablero de análisis).
- **Y dos comentarios que ya no decían la verdad.** `turnsOf` afirmaba que "una
  partida de sparring siempre arranca en la posición estándar, así que el
  índice es ya el ply absoluto", que es justo lo que RF-4.4 acaba de romper:
  dice ya lo que hay y remite a la fila 101, igual que el panel del origen en
  `SparringGamePage`. Y el módulo de la pantalla nueva no explicaba por qué
  enseña abierto lo que un puzzle esconde; ahora lo dice (ver abajo).

Y tres rupturas del patrón que se revisaron y se dejan como están:

- **La evaluación del error se enseña abierta**, y en el puzzle sin resolver se
  esconde. No es la misma pantalla con dos reglas: en el puzzle el dato es
  media respuesta —la API lo manda a `null` a propósito hasta que se cierra—, y
  aquí no hay nada que adivinar, se viene a jugar otra vez la posición y es
  justamente el número que dice por cuál empezar. Escrito en los dos lados,
  `features/training/ReplaysPage.tsx` y `routers/replays.py::ReplayPositionOut`,
  para que no se lea como un descuido.
- **La lista no se genera ni se guarda**, al revés que las dos pestañas
  gemelas, que tienen su botón "Generar puzzles" / "Generar líneas" y su cola
  con repasos. No arrastra estado propio, así que se deduce de los análisis que
  ya hay cada vez que se pregunta (ADR-0008). Por eso tampoco dice "N por
  repasar de M": lo que sí debería decir es cuántos errores hay y que enseña
  los veinte peores, y eso es la fila 102.
- **La pestaña se llama "Re-jugar" y sus hermanas "Puzzles", "Aperturas" y
  "Sparring".** Las otras tres nombran lo que se entrena; esta nombra lo que se
  hace, porque lo que se entrena —los errores propios— ya es lo que dan los
  puzzles, y la diferencia entre las dos pestañas está justamente en el verbo:
  allí se busca la jugada, aquí se vuelve a jugar la partida.

**2026-09-21 · el plan de entrenamiento semanal (RF-4.5).** La pantalla que
cierra RF-4 entero, y la primera de la sección que no entrena nada: dice **qué falla**, con su
número, y debajo **los deberes que salen de ahí**, con su avance. Abrió las
filas **104 a 106** —la 106 cerrada ese mismo día, cambiando el molde de la
frase por «están clasificados como «De final»», que encaja con las cuatro
etiquetas sin darles una segunda forma— y dejó ocho arreglos en el commit.

**El cambio de portada se revisó y está bien.** Entrar en "Entrenamiento" ya no
lleva a los puzzles sino al plan, y los puzzles pasan a `/training/puzzles`.
Es coherente con cómo se entra en las otras secciones: la portada de una
sección es la pantalla que da la vista de conjunto —Partidas es el listado,
Estadísticas es el panel—, no una de las herramientas. Y las cuatro pestañas
que quedan son justamente adonde manda el plan, así que la primera pantalla de
la sección responde a "¿por dónde empiezo?" en vez de dar por supuesto que la
respuesta son los puzzles. Nada enlazaba a `/training` contando con encontrar
los puzzles: el único enlace externo es el de la navegación principal, que
apunta a la sección y no a una pantalla.

Los arreglos:

- **C-2 · la barra de progreso es una sola.** La de las tarjetas de deberes
  estaba escrita a mano con el mismo alto, el mismo redondeo y el mismo
  `transition-all` que la de `ProgressBox`, cambiando solo de color: dos barras
  idénticas sostenidas a mano, que es la familia de las filas 39 a 41. Sale ya
  de `components/ProgressBar.tsx`, que usan las dos. Lo que las diferencia no
  es la forma sino **de quién es el avance** —el sistema trabajando frente a lo
  que lleva hecho quien entrena—, y eso es lo único que parametriza el tono.
- **C-4 · el vacío de las debilidades es el recuadro compartido.** "No he
  encontrado nada que destaque" era un `<p>` suelto dentro del panel, que es
  exactamente lo que el criterio prohíbe; es un `EmptyState`, como el "Sin
  discrepancias" de la comparación de motores, que fue la última frase suelta
  que hacía de vacío.
- **C-2 · el enlace de la tarjeta va en secundario.** Estaba en `primary`, así
  que con cuatro deberes había cuatro acciones principales en la misma
  pantalla, contra la regla escrita en `components/Button.tsx` —la misma que
  cerró la fila 61 y que se aplicó en RF-1.5 y en RF-6.7—. Queda en
  `secondary` y `sm`, que es como se ve el enlace que abre un elemento en los
  cuatro listados de la aplicación.
- **C-2 · el encabezado de sección, del tamaño de siempre.** "Tus deberes de
  esta semana" iba a `text-lg font-medium` y las ocho secciones del panel de
  estadísticas van a `font-semibold`: un noveno tamaño de rótulo para lo mismo.
- **C-5 · los puntos de precisión salen de un solo sitio.** "Tu precisión ha
  bajado 3.2 puntos" resolvía su decimal con un `.toFixed(1)` propio mientras
  la frase de tendencia del panel de estadísticas tenía el suyo, escondido en
  una función privada de `lib/insights.ts`. Sube a `formatAccuracyPoints` en
  `lib/format.ts` y lo usan las dos, como ya se hizo con `formatPerHundredMoves`.
- **C-5 · y los puntos de marcador también.** Lo que cuesta una apertura
  —`points_lost`, victorias y tablas frente a empatarlas todas— se formateaba
  a mano con su unidad pegada en la frase. Es `formatScorePoints`, para que
  ponerle nombre a esa magnitud (fila 104) sea un cambio en un solo sitio.
- **C-2 · la sub-navegación envuelve.** Con la quinta pestaña, `flex gap-1` sin
  `flex-wrap` se desborda en una ventana estrecha. Es lo mismo que le pasó a la
  fila de acciones del visor con su cuarto control, y se arregla igual.

Y un comentario que ya no decía la verdad: el módulo de `TrainingHeader`
afirmaba que a la sección "le falta todavía el plan semanal (RF-4.5)".

**2026-09-22 · la capa de ocupación en las pantallas de entrenamiento (RF-7.1 a
RF-7.7 sobre RF-4.1, RF-4.2 y RF-4.3).** La capa que hasta ahora tenían el
visor y el tablero de análisis entra también en el puzzle, en el drill de
apertura y en la partida de sparring —las tres pantallas de entrenamiento con
tablero; el plan, re-jugar y la antesala de sparring no lo tienen—. Con eso son
**cinco pantallas con la misma columna**: tablero, frase de atajos bajo él
(`BOARD_HINT_CLASSES`, con la misma frase del atajo `O` en las cinco) y panel
de ocupación debajo, que es donde la fila 90 lo dejó. La revisión abrió la
fila **107**, abrió y cerró la **108**, precisó la 91 y dejó estos arreglos en
el mismo commit:

- **C-2 · por qué aquí las marcas arrancan apagadas, dicho donde se ven
  apagadas.** Es la divergencia deliberada de este cambio: en el visor y en el
  tablero de análisis las tres marcas salen encendidas y en las tres de
  entrenamiento salen apagadas, porque rodear las piezas colgadas (RF-7.4) es
  media solución del puzzle y el aviso de blunder que un rival calibrado no
  debe dar. El panel era el mismo en los cinco sitios y no decía nada, así que
  quien llegaba desde el visor se encontraba las tres casillas desmarcadas sin
  explicación. El controlador expone ya `marksOnByDefault` —el mismo
  nombre con el que la pantalla lo pidió— y el panel escribe bajo "Qué se
  marca" que aquí arrancan apagadas y por qué, con la misma forma
  que las ayudas de cada casilla (fila 89). Una divergencia justificada que no
  se cuenta en pantalla se lee igual que un descuido.
- **C-3 · las tres casillas mandan sobre todo lo que la capa dice, no solo
  sobre lo que dibuja** (fila 108, abierta y cerrada aquí). `SquareInspection`
  escribía "· colgada" y "· clavada contra su rey" con esas marcas
  desmarcadas, y `AttackList` listaba los rayos X igual: en entrenamiento,
  donde arrancan apagadas justamente para no adelantar nada, pulsar una
  casilla entregaba en palabras lo que la casilla desmarcada prometía no
  dibujar, y apagar la marca quedaba en un gesto sin efecto. Ahora `marks`
  gobierna también la inspección. El conteo de atacantes y defensores no
  depende de ninguna marca: es RF-7.3 y es el trabajo del panel.
- **C-1 · el atajo `O` se anuncia en las cinco y con la misma frase.** La frase
  estaba escrita dos veces, una en el visor y otra en el tablero de análisis, y
  las tres pantallas nuevas habrían sido la tercera y la cuarta copia. Es
  `OCCUPANCY_TOGGLE_KEY_HINT`, exportada desde `useOccupancy.ts` —al lado de la
  tecla que nombra, que es lo que impide cambiar una sin la otra— y se compone
  con lo propio de cada pantalla: "Arrastra una pieza para responder…", "La
  línea terminó…", la leyenda de las flechas del puzzle resuelto.
- **Comentarios que dejaron de ser ciertos al pasar de dos pantallas a cinco.**
  `occupancy.ts`, `OccupancyPanel.tsx`, `OccupancyLayer.tsx`, `Chessboard.tsx`
  y las dos recetas de `components/styles.ts` decían "las dos pantallas" de lo
  que ahora comparten cinco; y `OccupancyLayer` y `SquareKeyboardGrid` decían
  que la capa entra por el hueco `overlay` de `Chessboard`, cuando desde este
  cambio entra por su propiedad `occupancyController` y la rejilla enfocable
  viaja dentro
  de la capa.

**2026-09-22 · el barrido de cierre de la fase 3.** Las quince filas que la
sección de Entrenamiento había ido abriendo, cerradas de una vez, que es como
se decidió el 2026-09-19 que se harían: solo con las seis pantallas delante se
puede decidir en qué se parecen. Seis de las quince pedían una decisión que no
era de código; van marcadas como tales.

- **91 · mover una pieza con el teclado** (C-1). Era la más vieja y la única
  que no se podía arreglar en su pantalla: los tableros donde se mueve —el
  puzzle, el drill, el sparring y el de análisis— solo se dejaban usar
  arrastrando, y la rejilla enfocable que ya existía (`SquareKeyboardGrid`)
  activa **una** casilla mientras que una jugada son dos. La solución no fue
  inventar el flujo de dos pasos sino devolvérselo a chessground: la rejilla
  vive ahora en `Chessboard` y activar una casilla llama a su `selectSquare`,
  que ya sabe tomar el origen con la primera pulsación y mover con la segunda.
  Esc suelta lo elegido. Como es una sola rejilla para los dos trabajos que
  tiene una casilla —mover e inspeccionar (RF-7.3)—, la de `OccupancyLayer`
  desapareció: dos rejillas superpuestas eran dos juegos de paradas de foco. El
  editor de posición conserva la suya por `overlay`, porque ahí activar una
  casilla es colocar una pieza.
- **92 · desde qué bando se cuenta la probabilidad de victoria** (C-5,
  *decisión*). La frase del error propio se queda contando desde quien jugó
  («Tu probabilidad de victoria pasó de…») y **el criterio C-5 es el que cede**:
  gana una excepción escrita para las frases que nombran el bando. Girarla a
  las blancas habría sido coherente con la fila 52, pero quien juega con negras
  leería «31 puntos más» delante de su propia equivocación, y lo que la fila 52
  arregló era un número suelto en una lista, que sigue prohibido.
- **94 · la partida de sparring se encabeza como pantalla de detalle** (C-2,
  *decisión*). Llevaba la cabecera de la sección, así que se titulaba
  «Entrenamiento», volvía atrás con un botón al final del lateral y la pestaña
  «Sparring» hacía lo mismo con otro nombre. Ahora lleva «← Volver a sparring»
  sobre un título que nombra la partida, como el visor y el tablero de
  análisis, y sin pestañas: una partida concreta no es una forma de entrenar
  entre cinco.
- **95 · un solo listado de panel** (C-2). La receta —panel sin relleno, `<ul>`
  dentro, filas separadas por una línea— estaba escrita a mano en el listado de
  sparring y copiada carácter a carácter en el de re-jugar. Es
  `components/PanelList.tsx` con `LIST_ROW_CLASSES` y `LIST_ROW_SUMMARY_CLASSES`
  en `styles.ts`, por lo mismo y con la misma forma que `DataTable`. No
  sustituye a `DataTable`: una fila de re-jugar se despliega para enseñar el
  formulario de dificultad.
- **96 · el nombre del rival se compone una vez** (C-5). Lo armaban el front
  (el desplegable de «Nueva partida») y el servidor (`opponent_name`), y
  coincidían carácter a carácter sin que nada lo garantizara. Es
  `formatOpponentName(engine, engineElo)` en `lib/format.ts`, y
  `opponent_name` sale de `SparringGameOut`: el `_opponent_name` del servidor
  se queda solo para la cabecera del PGN, que es un documento que se abre en
  otros programas y donde `[Black "lc0"]` no diría contra quién se jugó.
- **97 · fallar deja el tablero igual en las dos gemelas** (C-2 / C-3,
  *decisión*). Gana el puzzle, que es el que tenía la razón escrita: la jugada
  errónea se queda puesta y hace falta pulsar «Volver a intentarlo», porque
  borrarla al instante da la sensación de que la pieza rebotó y no de que la
  respuesta era otra. El drill dejó de aceptar la posición de vuelta del
  servidor como lo que se ve.
- **98 · el panel lateral se encabeza igual en las tres** (C-2 / C-3). El
  título es «Juegas con blancas/negras» en las tres, y la insignia dice siempre
  lo mismo —si el sistema está esperando, si te toca o si se acabó— en vez de
  significar el repaso en el puzzle, la baraja en el drill y el turno en el
  sparring. Es `features/training/ExerciseStatusBadge.tsx`. Lo que identifica al
  ejercicio bajó al cuerpo del panel, y de paso el drill enseña ya sus
  `repetitions`, que la API mandaba y nadie leía.
- **99 · que falte teoría es condición de la pantalla, no del botón** (C-3).
  `positions_missing` viaja ya en `DrillQueueOut` y no solo en
  `DrillGenerationOut`, de la misma `compare_repertoire` que lo cuenta al
  generar: el repertorio se llena a trozos (ADR-0010), así que
  una cola corta puede serlo porque falta teoría y no porque se juegue bien, y
  eso hay que poder saberlo al llegar y no después de pulsar «Generar líneas».
- **100 · la línea del drill se lee como notación** (C-5). Era la única
  secuencia de jugadas de la aplicación pintada como prosa. Es
  `formatMoveSequence` en `lib/moves.ts`, numerada y monoespaciada, con
  `startingPly` para las que no arrancan en la salida.
- **101 · una partida retomada se numera desde donde empieza** (C-5).
  `SparringGameOut` manda `starting_ply`, sacado de `starting_fen` y no de
  `origin_ply` —que es relativo al inicio de la partida de origen y da otro
  número si esa no empezaba en la salida—, y con él numeran tanto la lista de
  jugadas como la frase «Retomada desde la jugada 23».
- **102 · re-jugar dice cuántos errores hay** (C-3). La respuesta es ya
  `ReplayQueueOut` —`positions` y `total`—, con el total en el cuerpo y no en
  una cabecera `X-Total-Count` como el listado de Partidas, porque las tres
  pestañas hermanas lo traen así y es con ellas con las que se compara al
  cambiar de pestaña.
- **103 · las ayudas salen de los `title`** (C-6 / C-7). Las tres acciones que
  sacan la partida del visor —«Exportar PGN anotado», «Abrir como tablero» y
  «Jugar desde aquí»— explicaban qué hacen en un `title`, que con teclado no
  aparece nunca y en un botón deshabilitado tampoco. Están a la vista bajo la
  fila de acciones, como ya lo hacían Puzzles y Aperturas bajo su botón de
  generar, y de paso el «Abrir como tablero» del sparring, que tenía el mismo
  defecto en la misma acción.
- **104 · cada magnitud dice de qué son sus puntos** (C-5 / C-6, *decisión*).
  «Puntos» nombraba tres cosas seguidas en la misma lista del plan. Ahora son
  «pts de prob. de victoria», «puntos de marcador» y «puntos de precisión», y
  la de la apertura dice además frente a qué se pierden: «frente a empatarlas
  todas», que es la referencia de `points_lost` y la mitad que faltaba.
- **105 · la tarjeta se llama como el sitio al que lleva** (C-2, *decisión*).
  Las tarjetas de deberes decían «Líneas de apertura», «Posiciones a re-jugar»
  y «Partidas contra el motor» y se aterrizaba en «Aperturas», «Re-jugar» y
  «Sparring». Manda el nombre de la pestaña; lo que la tarjeta hace lo cuenta
  la frase de debajo, que es donde ya estaba.
- **107 · el tablero se dibuja de un solo tamaño** (C-2, *decisión*). La medida
  vive en `components/board/BoardFrame.tsx`, que usan las cinco pantallas con
  tablero, y no en `Chessboard`: el editor de posición no tiene por qué
  heredarla.
- **109 · la acción de la partida de sparring sube a la cabecera** (C-2).
  Abierta y cerrada aquí, y nacida de la 94: en cuanto la pantalla se encabeza
  como pantalla de detalle, se compara con el visor y con el tablero de
  análisis también por dónde tiene sus acciones, y «Abrir como tablero» —el
  mismo nombre en las tres— estaba al final del lateral, bajo la lista de
  jugadas. Sube a la derecha del título, con su línea de ayuda debajo y con el
  recuadro de error al lado del botón que lo provoca, que estaba a dos columnas
  (criterio C-3). Con ella sube «Abandonar», que es la que ocupa ese sitio
  mientras se juega.

Y cinco arreglos mecánicos, de comprobar el barrido leyendo las cinco pantallas
con tablero estado por estado, sin nada que decidir:

- **C-1 · el teclado se anuncia solo donde el tablero acepta jugadas.**
  `KEYBOARD_MOVE_HINT` se encadenaba siempre, así que el puzzle cerrado, la
  línea terminada y la partida acabada decían «el tablero ya no se mueve» y a
  continuación «Intro elige origen y destino», en la misma frase; y con la
  jugada errónea encima, esperando a «Volver a intentarlo», lo mismo. Va ahora
  donde va la invitación a arrastrar y no más: las dos vías se prometen juntas,
  que es lo que pide C-1. En el tablero de análisis sigue saliendo siempre,
  porque allí el tablero siempre acepta jugadas.
- **C-3 · un tablero que deja de aceptar jugadas deja de aceptarlas.** Quitarle
  `legalMoves` no bastaba: `buildBoardConfig` omite `movable` cuando no las hay
  —mandarlo en `undefined` le borraría a chessground ese trozo de estado— y
  chessground conserva entonces los destinos de la posición anterior, así que
  las piezas se seguían arrastrando sobre el puzzle fallado y el tablero
  quedaba enseñando una posición que no era la de nadie. `Chessboard` le manda
  ya los destinos vacíos. Con eso, el puzzle cierra su tablero al cerrarse y
  mientras el servidor comprueba, que es la misma regla que ya tenían el drill
  y el sparring (`canMove`).
- **C-3 · las tres marcas mandan también en lo que se lee en voz alta.** La
  fila 108 las hizo gobernar la inspección del panel, pero la rejilla enfocable
  que se mudó a `Chessboard` seguía diciendo «clavada» y «colgada» en el
  `aria-label` de cada casilla con esas marcas apagadas: con teclado y lector
  de pantalla, apagarlas volvía a ser un gesto sin efecto justo en las tres
  pantallas donde arrancan apagadas. `describeSquareOccupancy` recibe las
  marcas, como `SquareInspection`.
- **C-2 · la frase del teclado del editor de posición, con las mismas
  palabras.** Decía «Con teclado: tabula hasta el tablero, muévete con las
  flechas y pon la pieza elegida con Intro» para la misma rejilla que las otras
  cinco pantallas anuncian como «Con el teclado: Tab lleva al tablero, las
  flechas recorren las casillas…». Lo que cambia es lo que hace Intro, que es
  lo único que cambia ahora en la frase.
- **Comentarios y READMEs que dejaron de ser ciertos.** `TrainingHeader` y
  `features/training/README.md` seguían diciendo que las **seis** pantallas de
  la sección comparten cabecera, cuando la fila 94 sacó de ahí a la partida de
  sparring; y los cuatro archivos que estrenó el barrido —`PanelList`,
  `BoardFrame`, `board/hints.ts` y `ExerciseStatusBadge`— no estaban en la tabla de su
  README, que es donde se mira antes de copiar una receta a mano.


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
   desde el 109— en vez de dejarla suelta. Una fila se borra cuando se arregla,
   y las demás no se renumeran: el número es la referencia con la que se habla
   de ella en un commit o en una revisión.
