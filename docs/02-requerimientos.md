# 02 · Requerimientos

> **Alcance de la versión 1.0.** Todo lo listado en este documento (RF-1 a RF-7,
> RNF-1 a RNF-10) a fecha **2026-09-05** es el alcance esperado de LUCIA
> **v1.0.0**, con independencia de su prioridad P0/P1/P2 — P2 significa
> "deseable dentro de 1.0", no "para después". Cualquier requerimiento que se
> añada después de esa fecha va a [Post 1.0 (futuro)](#post-10-futuro), al
> final de este documento, y no participa del conteo de progreso hacia 1.0.0 en
> [docs/05-roadmap.md](05-roadmap.md) hasta que se decida moverlo al alcance de
> una versión de forma explícita. Lo vigila el agente `versionador`.

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
| RF-5.2 | Explorar variantes del motor desde cualquier posición (análisis en vivo, flechas de mejores jugadas). | P0 |
| RF-5.3 | Listado y filtrado de partidas (fecha, color, resultado, apertura, control, rival). | P0 |
| RF-5.4 | Panel de configuración de motores (ruta, hilos, hash, profundidad, MultiPV, red de Lc0). | P0 |
| RF-5.5 | Exportar partida analizada a PGN con comentarios y variantes. | P1 |
| RF-5.6 | Tema oscuro/claro, responsive. | P1 |

### RF-6 · Tablero de análisis (partidas "IRL" y posiciones libres)

Espacio de trabajo independiente del historial de chess.com, al estilo de los tableros de análisis de nextchessmove / lichess study. Sirve para partidas presenciales (OTB), posiciones de libros, tácticas de clase o cualquier idea propia.

| ID | Requerimiento | Prioridad |
| ---- | --------------- | ----------- |
| RF-6.1 | Crear un tablero de análisis desde: posición inicial, FEN, PGN pegado, o editor de posición (colocar/quitar piezas, turno, enroques, al paso). | P0 |
| RF-6.2 | Introducir jugadas a mano sobre el tablero y obtener análisis del motor en vivo (mismas capacidades que RF-5.2: MultiPV, flechas, eval). | P0 |
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
inicio de este documento). Mismo formato que las secciones anteriores (RF-8 en
adelante), pero no cuentan para el progreso hacia 1.0.0 hasta que se muevan
explícitamente al alcance de una versión.

*(vacío por ahora)*
