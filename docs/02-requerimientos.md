# 02 · Requerimientos

> **Alcance de la versión 1.0.** Todo lo listado en este documento (RF-1 a RF-7,
> RNF-1 a RNF-10) a fecha **2026-09-05** es el alcance esperado de LUCIA
> **v1.0.0**, con independencia de su prioridad P0/P1/P2 — P2 significa
> "deseable dentro de 1.0", no "para después". Cualquier requerimiento que se
> añada después de esa fecha va a [Post 1.0 (futuro)](#post-10-futuro), al
> final de este documento, y no participa del conteo de progreso hacia 1.0.0 en
> [docs/05-roadmap.md](05-roadmap.md) hasta que se decida moverlo al alcance de
> una versión de forma explícita. Lo vigila el agente `versionador`.
>
> **Ampliación del 2026-09-06.** RF-10 (alternativas por jugada en el análisis
> guardado) se planteó después del corte y se movió al alcance de v1.0 el mismo
> día, por decisión expresa: persistir las líneas del motor es un cambio de
> esquema y del flujo de análisis, y dejarlo para después de 1.0 obligaría a
> migrar la base o a re-analizar partidas ya analizadas. El resto de lo añadido
> tras el corte (RF-8, RF-9 y RNF-11) sigue fuera, porque es interfaz sobre
> datos que ya existen y no cuesta más hacerlo después.
>
> **Ampliación del 2026-09-07.** RF-11 (partidas con ventaja contra el motor)
> se plantea después del corte y se queda fuera del alcance de v1.0: necesita
> antes el editor de posición pieza a pieza (RF-6.1, fase 2) y el sparring
> contra motor con fuerza calibrada (RF-4.3, fase 3), que sí son alcance de
> 1.0, y no cambia el esquema de la base ni obliga a re-analizar nada.
>
> Ese mismo día se **reescribieron los textos de RF-5.2 y RF-6.2**, que estaban
> resumidos en una línea ("análisis en vivo, flechas de mejores jugadas"), para
> decir qué se ve exactamente sobre el tablero: MultiPV, flechas etiquetadas,
> barra de evaluación en probabilidad de victoria y previsualización de la
> continuación. No es alcance nuevo pendiente —lo descrito ya está entregado o
> repartido entre ítems existentes de la fase 2—, pero queda anotado aquí
> porque toca dos requerimientos congelados y nadie debería enterarse por un
> `git blame`.

Prioridad: **P0** = MVP imprescindible · **P1** = siguiente iteración · **P2** = deseable.

## Requerimientos funcionales

### RF-1 · Importación de datos de chess.com

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-1.1 | Importar perfil público (username, ratings por control de tiempo, país, fecha de alta). | P0 |
| RF-1.2 | Importar historial completo de partidas vía archivos mensuales (`/pub/player/{user}/games/{YYYY}/{MM}`), con PGN, relojes por jugada (`%clk`), resultado, ECO, precisión reportada. | P0 |
| RF-1.3 | Sincronización incremental: solo descargar meses nuevos o el mes actual. | P0 |
| RF-1.4 | Respetar rate limits y `User-Agent` requerido por chess.com; reintentos con backoff. | P0 |
| RF-1.5 | Importar PGN manual (archivo) para partidas de otras fuentes (OTB, lichess). | P1 |
| RF-1.6 | Importar historial de rating y estadísticas (`/pub/player/{user}/stats`). | P1 |

### RF-2 · Análisis con motores

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-2.1 | Analizar cada jugada de una partida con Stockfish vía UCI: eval (cp / mate), mejor línea, MultiPV configurable. | P0 |
| RF-2.2 | Clasificar cada jugada: *Mejor, Excelente, Buena, Libro, Imprecisión, Error, Blunder, Perdió el mate* — replicando la "Game Review" pero con umbrales documentados y ajustables. | P0 |
| RF-2.3 | Calcular precisión por jugador y por fase (apertura / medio juego / final) con fórmula documentada (basada en *win probability*, no en cp crudos). | P0 |
| RF-2.4 | Análisis en background con cola de trabajos; la UI muestra progreso. | P0 |
| RF-2.5 | Análisis en lote: "analiza mis últimas N partidas" o "todo 2025". | P0 |
| RF-2.6 | Análisis con Lc0 como segunda opinión: probabilidad W/D/L, contraste con Stockfish en posiciones donde discrepan. | P1 |
| RF-2.7 | Caché de evaluaciones por FEN para no re-computar posiciones repetidas (aperturas). | P1 |
| RF-2.8 | Detección de momentos críticos: jugada única, cambio de signo de eval, oportunidad táctica perdida. | P1 |
| RF-2.9 | Explicación en lenguaje natural de por qué una jugada es error (basada en heurísticas: pieza colgada, mate en N, pérdida de material, etc.). | P2 |

### RF-3 · Estadísticas e insight

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-3.1 | Dashboard: rating por control de tiempo, W/D/L, racha, partidas por mes. | P0 |
| RF-3.2 | Rendimiento por apertura (ECO / nombre) con blancas y negras: % victoria, precisión media, eval promedio al salir de la apertura. | P0 |
| RF-3.3 | Rendimiento por fase: dónde pierdo más eval (apertura, medio juego, final). | P0 |
| RF-3.4 | Distribución de errores: blunders por tipo (táctico, posicional, final, gestión de tiempo). | P1 |
| RF-3.5 | Gestión de tiempo: relación entre tiempo restante y calidad de jugada; detectar *time trouble* recurrente. | P1 |
| RF-3.6 | Comparación de repertorio con teoría (Lichess Opening Explorer / base de maestros): dónde me salgo de la línea principal y con qué resultado. | P1 |
| RF-3.7 | Tendencias: evolución de precisión y tipo de errores en el tiempo. | P1 |
| RF-3.8 | Análisis de rivales: patrones contra rivales recurrentes. | P2 |

### RF-4 · Entrenamiento

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-4.1 | Puzzles generados desde mis propios errores: posición antes del blunder, encontrar la mejor jugada. Con repetición espaciada. | P1 |
| RF-4.2 | Drill de aperturas: repetir las líneas donde mi rendimiento es peor. | P1 |
| RF-4.3 | Sparring contra motor con fuerza calibrada (Stockfish `UCI_LimitStrength` / `UCI_Elo`, o Lc0 con redes "Maia"-like para estilo humano). | P1 |
| RF-4.4 | "Re-juega desde el error": retomar una partida propia desde la posición del blunder contra el motor. | P2 |
| RF-4.5 | Plan de entrenamiento semanal generado a partir de las debilidades detectadas. | P2 |

### RF-5 · Interfaz

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-5.1 | Visor de partida: tablero interactivo, lista de jugadas con clasificación, gráfico de evaluación, navegación con teclado. | P0 |
| RF-5.2 | Explorar variantes del motor desde cualquier posición, y verlas **sobre el tablero**, no solo como texto: análisis en vivo con MultiPV, flechas de las mejores líneas (la mejor destacada, las siguientes atenuadas, cada una con su evaluación en la etiqueta), barra de evaluación en probabilidad de victoria junto al tablero, y previsualización de la continuación al recorrer el panel del motor. | P0 |
| RF-5.3 | Listado y filtrado de partidas (fecha, color, resultado, apertura, control, rival). | P0 |
| RF-5.4 | Panel de configuración de motores (ruta, hilos, hash, profundidad, MultiPV, red de Lc0). | P0 |
| RF-5.5 | Exportar partida analizada a PGN con comentarios y variantes. | P1 |
| RF-5.6 | Tema oscuro/claro, responsive. | P1 |

### RF-6 · Tablero de análisis (partidas "IRL" y posiciones libres)

Espacio de trabajo independiente del historial de chess.com, al estilo de los tableros de análisis de nextchessmove / lichess study. Sirve para partidas presenciales (OTB), posiciones de libros, tácticas de clase o cualquier idea propia.

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-6.1 | Crear un tablero de análisis desde: posición inicial, FEN, PGN pegado, o editor de posición (colocar/quitar piezas, turno, enroques, al paso). | P0 |
| RF-6.2 | Introducir jugadas a mano sobre el tablero y obtener análisis del motor en vivo, con las mismas capacidades visuales que RF-5.2: MultiPV, flechas de las mejores líneas, barra de evaluación y previsualización de la continuación. | P0 |
| RF-6.3 | Árbol de variantes: crear ramas desde cualquier jugada, promover una variante a línea principal, borrar una variante o "borrar desde aquí", anidar sin límite. | P0 |
| RF-6.4 | Guardar el tablero con nombre, etiquetas y comentarios por jugada. Listar, buscar, editar y eliminar tableros guardados. Todo persiste en la base local. | P0 |
| RF-6.5 | Independencia total del historial: los tableros de análisis no cuentan en estadísticas ni en detección de patrones (RF-3) salvo que el usuario los marque explícitamente como "partida propia" (p. ej. una OTB donde jugó él). | P0 |
| RF-6.6 | Abrir cualquier partida importada de chess.com "como tablero de análisis" (copia desacoplada) para explorar sin alterar el análisis original. | P1 |
| RF-6.7 | Importar/exportar el tablero completo como PGN con variantes y comentarios (compatible con lichess, ChessBase, SCID). | P1 |
| RF-6.8 | Autoguardado y control de versiones simple (deshacer/rehacer sobre el árbol). | P1 |
| RF-6.9 | Análisis completo del tablero en background (clasificación de jugadas y precisión como en RF-2) si el usuario lo pide. | P1 |

### RF-7 · Ocupación del tablero (control de casillas)

Capa de visualización activable con una tecla sobre **cualquier tablero** (visor RF-5, tablero de análisis RF-6, entrenamiento RF-4). No es un modo aparte: no obliga a salir de lo que se está haciendo. Se calcula en el cliente con chess.js, sin motor.

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-7.1 | **Sub-modo "Mapa de calor".** Cada casilla se colorea según el balance de atacantes directos blancos y negros: dominio blanco, dominio negro, disputada, sin control. Intensidad proporcional al número de atacantes. | P1 |
| RF-7.2 | **Sub-modo "Cobertura directa".** Muestra solo el bando que tiene el turno (con toggle para ver el otro): las casillas que sus piezas cubren directamente y conectores pieza → casilla. Al pasar el ratón sobre una pieza se filtra a su cobertura; al hacer clic se fija. | P1 |
| RF-7.3 | **Inspección por casilla.** Clic en una casilla: lista de atacantes y defensores de ambos bandos ordenados por valor de pieza. | P1 |
| RF-7.4 | **Piezas colgadas.** Marca las piezas atacadas y no defendidas, o atacadas por una pieza de menor valor. | P1 |
| RF-7.5 | **Solo ataques directos en el mapa.** Los rayos X (batería propia: torre tras torre; o a través de pieza rival: dama-caballo-rey) se dibujan aparte con línea discontinua o color atenuado, nunca se suman al balance de RF-7.1. | P1 |
| RF-7.6 | **Piezas clavadas.** Una pieza clavada al rey sigue contando como atacante (da jaque si captura), pero se marca de forma distinta porque no puede moverse legalmente. | P1 |
| RF-7.7 | **Reglas de conteo.** El rey cuenta como atacante. Los peones cuentan por sus capturas en diagonal, no por su avance. La casilla de captura al paso cuenta como atacada por el peón correspondiente. | P1 |
| RF-7.8 | Persistencia de preferencias: sub-modo y filtros activos se recuerdan entre sesiones. | P2 |
| RF-7.9 | "Casillas críticas según motor": superponer las casillas que más aparecen en las mejores líneas de Stockfish. Único punto de RF-7 que requiere motor. | P2 |

### RF-10 · Alternativas por jugada en el análisis guardado

Añadido al alcance de v1.0 el 2026-09-06 (ver la nota de alcance al inicio del
documento). Las flechas múltiples de RF-5.2 hoy solo existen en el tablero de
análisis, porque ahí el motor responde en vivo sobre la posición actual. En el
visor de una partida analizada solo hay una flecha, y no por decisión de
interfaz: el análisis guardado no tiene las alternativas. `analyzed_moves`
guarda una única `best_move_uci` por jugada, aunque el análisis se haya corrido
con MultiPV.

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-10.1 | Persistir las N mejores líneas de cada posición analizada, no solo la mejor, para que el visor pueda enseñar las alternativas de cada jugada como ya hace el tablero de análisis. | P1 |
| RF-10.2 | Usar esas alternativas en el visor: flechas múltiples por jugada y "lo que podrías haber jugado en su lugar" al pararse en un error. | P1 |
| RF-10.3 | Usar esas alternativas en entrenamiento: un puzzle generado desde un error propio (RF-4.1) necesita saber qué jugadas eran buenas, no solo cuál era la mejor, para aceptar respuestas equivalentes en vez de exigir la única del motor. | P2 |

Notas técnicas, para cuando se implemente (fase 2 del roadmap):

- **El dato puede estar ya en la base.** `position_cache.lines_json` guarda
  **todas** las líneas del MultiPV por FEN (RF-2.7), así que para las partidas
  analizadas recientemente las alternativas se pueden recuperar sin volver a
  gastar motor. Lo que falta es una vía para leerlas y la garantía de que no se
  hayan quedado obsoletas por un cambio de configuración, porque la clave de la
  caché incluye motor, red, profundidad y MultiPV.
- **Se solapa con RF-2.8** ("momentos críticos, con MultiPV real en la
  clasificación", pendiente en la fase 2): distinguir una jugada única de una
  con tres alternativas igual de buenas necesita exactamente el mismo material.
  Conviene resolverlos juntos y no dos veces.

## Requerimientos no funcionales

| ID | Requerimiento |
| ---- | --------------- |
| RNF-1 | **Local-first**: la app funciona 100% offline tras la importación inicial. Sin servicios de pago. |
| RNF-2 | **Rendimiento**: análisis de una partida de 40 jugadas a profundidad 18 en < 60 s en CPU de escritorio moderna (Stockfish, 4 hilos). Análisis en lote paralelizable por número de núcleos. |
| RNF-3 | **Reproducibilidad**: la misma partida + misma config de motor produce la misma clasificación (fijar hilos=1 y `nodes` en lugar de tiempo cuando se requiera determinismo). |
| RNF-4 | **Portabilidad**: Linux primero (Fedora, entorno del autor), después macOS y Windows. Docker como alternativa. |
| RNF-5 | **Licencia**: GPL-3.0 en todo el repo, compatible con Stockfish y Lc0. |
| RNF-6 | **Observabilidad**: logs estructurados; progreso de análisis visible; errores del motor capturados y reportados. |
| RNF-7 | **Datos**: base de datos local en SQLite (un archivo, respaldable). Migraciones versionadas. |
| RNF-8 | **Calidad**: tests unitarios para clasificación de jugadas y cálculo de precisión (son el corazón del producto); CI en cada push. |
| RNF-9 | **Extensibilidad**: cualquier motor UCI debe poder enchufarse (Komodo, Berserk, etc.) sin cambiar el núcleo. |
| RNF-10 | **Respeto a terceros**: cumplir los términos de la API pública de chess.com (User-Agent identificable, no scraping, no paralelismo agresivo). |

## Post 1.0 (futuro)

Requerimientos que surjan después de fijado el alcance de v1.0 (ver nota al
inicio de este documento). Mismo formato que las secciones anteriores (RF-8 y
RNF-11 en adelante), pero no cuentan para el progreso hacia 1.0.0 hasta que se muevan
explícitamente al alcance de una versión. La prioridad P0/P1/P2 de esta sección
es relativa entre sus propios requerimientos, no contra el alcance de 1.0: aquí
un P2 no significa "deseable dentro de 1.0", sino "de lo de aquí, lo menos
urgente".

### RF-8 · Personalización de interfaz

Apariencia y comportamiento de la UI más allá del tema claro/oscuro que ya
cubre RF-5.6. Nace de usar la aplicación: lo que hoy está fijado en el código
—la paleta de Tailwind, el tablero `brown` y las piezas `cburnett` importadas
en `apps/web/src/index.css`, los colores de clasificación de jugada— pasa a
ser elección del usuario. Todo se guarda como preferencias locales y comparte
almacén con RF-7.8 (persistencia del sub-modo de ocupación), que hoy es un
`localStorage` suelto por pantalla.

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-8.1 | **Tablero y piezas.** Set de piezas seleccionable (cburnett, merida, alpha…), color o textura del tablero, coordenadas dentro/fuera/ocultas, y estilo del resaltado de última jugada y casilla seleccionada. Chessground lo resuelve por CSS, así que es exponer los temas que ya trae y persistir la elección en vez de importar uno fijo. | P1 |
| RF-8.2 | **Paletas de la aplicación.** Temas de color nombrados más allá de claro/oscuro, incluyendo uno de alto contraste y uno apto para daltonismo (deuteranopía / protanopía). | P1 |
| RF-8.3 | **Colores semánticos, aparte de la paleta.** Clasificaciones de jugada (RF-2.2), mapa de calor de ocupación (RF-7.1) y flechas del motor (RF-5.2) se configuran por separado del tema general, **incluido el color propio de cada motor y el de "ambos coinciden"** que introduce RF-9.3. Es donde el daltonismo duele de verdad: hoy verde y rojo cargan solos con todo el significado, sin forma ni texto que los respalde. | P1 |
| RF-8.4 | **Layout.** Disposición de paneles (motor y variantes a izquierda o derecha, paneles plegables), tamaño del tablero frente al panel lateral, y recordar la elección por pantalla (visor, tablero de análisis, entrenamiento). | P2 |
| RF-8.5 | **Densidad y tipografía.** Modo compacto/cómodo para listas de jugadas y tablas, y tamaño de fuente ajustable sin romper el layout. | P2 |
| RF-8.6 | **Sonido.** Sonidos de jugada, captura, jaque y fin de partida, con volumen y apagado. Silencio por defecto. | P2 |
| RF-8.7 | **Animación y movimiento reducido.** Velocidad de la animación de las piezas y opción de desactivarla, respetando `prefers-reduced-motion` del sistema como valor inicial. | P2 |
| RF-8.8 | **Atajos de teclado reconfigurables**, con la lista consultable desde la propia app. Hoy las flechas ← → están fijadas en el código de cada pantalla. | P2 |
| RF-8.9 | **Presets.** Exportar e importar la configuración de apariencia como un archivo, para llevarla entre máquinas. | P2 |

### RF-9 · Comparación de evaluaciones entre motores

Amplía RF-2.6, que hoy se queda en el resumen de discrepancias: el panel del
visor lista solo las jugadas donde los dos motores se separan más de 10 puntos
de probabilidad de victoria, y como mucho ocho. Lo que falta es poder ver las
dos evaluaciones **una al lado de la otra en toda la partida**, coincidan o no.
Aplica solo cuando la partida tiene dos análisis terminados con motores
distintos.

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-9.1 | Tabla comparativa jugada a jugada con la evaluación de cada motor en columnas separadas. No necesita ser exhaustiva en su primera versión: basta con ver ambos resultados a la vez. | P2 |
| RF-9.2 | Detalle ampliado de una jugada de esa tabla: mejor línea de cada motor, diferencia de probabilidad de victoria y clasificación que le da cada uno. **Dónde vive está sin decidir** — pantalla aparte, modal sobre el visor o panel desplegable; se elige al implementarlo, no antes. | P2 |
| RF-9.3 | **Flechas de los dos motores sobre el mismo tablero.** Donde ambos recomiendan la misma jugada, una sola flecha en el color de acuerdo (hoy el verde y sus tonos, que es lo que ya hace RF-5.2 con un motor). Donde discrepan, una flecha por motor, cada una con su color propio. El tope de tres flechas con que se implementó RF-5.2 (una constante, no parte del requerimiento) se relaja en ese caso: una discrepancia son dos flechas, y verla es justo el objetivo. Los colores son configurables por RF-8.3. | P2 |
| RF-9.4 | **Cada línea dice qué motor la firma.** El panel del motor identifica de quién es cada evaluación —"Stockfish dice…", "Lc0 dice…"— y deja elegir motor donde hoy no se puede. Con un solo motor activo es un problema de coherencia ya abierto (fila 29 del inventario de [docs/07-coherencia-ui.md](07-coherencia-ui.md): el tablero de análisis evalúa sin decir con qué motor); con dos es imprescindible, porque sin ello dos flechas de colores distintos no significan nada. | P2 |

Nota técnica, para cuando se retome: el dato ya existe y no hace falta endpoint
nuevo. `GET /analysis/{id}` devuelve todas las jugadas de un análisis con su
`win_percent_after`, su `classification` y su `best_move_uci`, así que la tabla
se puede construir en el cliente pidiendo los dos análisis, que la pantalla ya
sabe identificar. `GET /analysis/compare` sigue sirviendo para el resumen de
discrepancias, que es otra vista del mismo material.

### RF-11 · Partidas con ventaja (odds) contra el motor

Jugar contra el motor desde una posición inicial elegida por el usuario, con
ventaja material para uno de los dos bandos. Nace de las propias partidas
importadas: chess.com ofrece *odds chess* y LUCIA ya las trae, así que el
formato es familiar y ya se sabe analizar. La idea es usar la ventaja como
segunda perilla de dificultad, independiente de la fuerza del motor: un jugador
de 1000 contra un motor calibrado a 700 pero con una torre de más para el
motor es un rival ajustado que ningún Elo por sí solo consigue.

**No reinventa lo que ya está en v1.0.** El editor de posición pieza a pieza es
RF-6.1 (fase 2) y el sparring contra motor con fuerza calibrada es RF-4.3
(fase 3); RF-11 es lo que falta para juntarlos: la ventaja material como parte
de la dificultad, y una partida jugada que se guarda y se analiza.

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-11.1 | Jugar una partida completa contra el motor desde una posición inicial personalizada —la del editor de RF-6.1 o un FEN— eligiendo color y bando con ventaja antes de empezar. | P1 |
| RF-11.2 | Dificultad en dos perillas independientes y combinables: fuerza del motor (RF-4.3: `UCI_Elo`/`UCI_LimitStrength` en Stockfish, red tipo Maia en Lc0) y ventaja material de la posición inicial. La pantalla deja claro cuál es cada una: no es lo mismo un motor débil que un motor fuerte con piezas de menos. | P1 |
| RF-11.3 | La partida jugada se guarda con su PGN (`[SetUp "1"]` + `[FEN ...]`), se puede analizar con RF-2 y recorrer en el visor (RF-5.1), pero **no cuenta** en estadísticas ni en detección de patrones (RF-3), igual que los tableros de análisis en RF-6.5: una partida contra un motor mutilado no dice nada del rendimiento real. | P1 |

Notas técnicas, para cuando se retome:

- **El análisis ya sabe partir de una posición no estándar.** Hasta el
  2026-09-07 `run_analysis` replicaba las jugadas sobre el tablero inicial de
  siempre, así que las partidas con `[SetUp "1"]` daban posiciones imposibles;
  ahora arranca de `pgn_game.board()`, que además marca Chess960 cuando toca.
  Una partida con ventaja se analiza hoy sin tocar nada más.
- **Lo que falta de verdad es jugar.** No hay ningún flujo en el que el motor
  responda a una jugada del usuario: `EngineBridge` solo analiza. RF-4.3 y
  RF-4.4 comparten esa carencia, y conviene resolverla una vez para los tres.

### Requerimientos no funcionales (Post 1.0)

| ID | Requerimiento |
| ---- | --------------- |
| RNF-11 | La interfaz se comporta igual en todas las pantallas: paridad entre lo que se puede hacer con el teclado y lo que hay como control visible, mismo nombre y misma posición para la misma acción, estados explícitos de lo que está haciendo el sistema (en cola, trabajando con progreso, listo, vacío, error), estados de carga/error/vacío compartidos, un solo formato por dato, y ningún número del motor sin etiqueta o representación visual que lo explique. Los criterios verificables y el inventario de incumplimientos actuales están en [docs/07-coherencia-ui.md](07-coherencia-ui.md). |
