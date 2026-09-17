# ADR-0010 · La comparación de repertorio consulta a Lichess, y lo guarda todo

- **Estado**: aceptado
- **Fecha**: 2026-09-10
- **Contexto**: RF-3.6 (comparación de repertorio con teoría), RNF-1
  (local-first), RNF-10 (respeto a terceros)

## Contexto

RF-3.6 pide comparar el repertorio propio con la teoría: dónde me salgo de la
línea principal y con qué resultado. "La teoría" es una base de partidas de
maestros, y LUCIA no la tiene: son millones de partidas, no caben en el
repositorio como cupo la tabla ECO (ADR-0009, 427 KB). La fuente elegida en
[docs/04-stack-tecnologico.md](../04-stack-tecnologico.md) es el **Opening
Explorer de Lichess**, gratuito y sin autenticación.

Eso choca de frente con RNF-1: *"la app funciona 100 % offline tras la
importación inicial"*. Es el primer requerimiento que necesita red **mientras
se usa la aplicación**, no solo al importar.

## Decisión

**Se consulta a Lichess, se guarda todo lo consultado, y la comparación se
calcula siempre sobre lo guardado.** En concreto:

0. **Con token.** El explorador dejó de admitir peticiones anónimas: responde
   `401` a todo, incluido el ejemplo de su propia documentación, y su
   especificación declara `security: OAuth2`. El token es gratuito, no necesita
   permisos y se configura en `LICHESS_TOKEN`. Sin él, la pantalla lo dice
   antes de que se pulse nada y sigue enseñando lo ya consultado.

1. **Dos operaciones separadas, y la separación es la decisión.**
   `GET /repertoire` **nunca** sale a internet: compara con lo que haya en la
   caché y dice cuántas posiciones le faltan por saber.
   `POST /repertoire/refresh` es lo único que consulta, y solo cuando el
   usuario lo pide.
2. **Todo lo consultado se guarda** en `explorer_positions`, indexado por EPD.
   La teoría de una posición no cambia de un día para otro, así que una vez
   preguntada vale para siempre y para todas las partidas que pasen por ahí.
3. **Se pregunta lo mínimo.** Solo por las posiciones en las que le toca mover
   al jugador, solo hasta la jugada 8 de cada bando, y solo hasta que la
   partida se sale del libro: en cuanto se sale, lo que venga después no dice
   nada del repertorio.
4. **Se pregunta despacio y con tope.** Una posición por segundo
   (`EXPLORER_MIN_INTERVAL_SECONDS`) y como mucho unas decenas por llamada, con
   backoff ante `429`. Completar un historial grande lleva varias pulsaciones,
   y la pantalla lo dice.

## Consecuencias

- **RNF-1 no se rompe, se lee con precisión.** Sin conexión, todo LUCIA
  sigue funcionando, incluida esta pantalla: enseña la comparación con lo que
  ya sabe y avisa de lo que le falta. Lo único que no se puede hacer sin red es
  **ampliar** el conocimiento de teoría. Esa frase —"todo funciona offline
  salvo traer teoría nueva"— es el contrato, y es más honesto que dejar RNF-1
  diciendo "100 %" sin matiz o que reescribir un requerimiento congelado.
- **La comparación puede estar incompleta, y eso se enseña.** `positions_missing`
  viaja en la respuesta y la pantalla lo dice siempre. Una comparación a medias
  que se presenta como completa mentiría sobre el repertorio del usuario.
- **La primera vez es lenta a propósito.** Un historial de 324 partidas necesita
  cientos de posiciones; a una por segundo son minutos repartidos en varias
  pulsaciones. Se prefiere eso a golpear un servicio gratuito ajeno (RNF-10),
  que además acabaría limitándonos.
- **Si Lichess cambia o desaparece, se degrada, no se rompe.** El fallo se
  distingue (`LichessExplorerError` → 502 con el motivo), lo ya guardado sigue
  sirviendo, y sustituir la fuente es cambiar `packages/lichess` sin tocar el
  servicio ni la pantalla.
- **La caché es desechable.** `explorer_positions` se puede vaciar entera sin
  perder nada propio: se vuelve a preguntar. No es un dato del usuario, es una
  copia local de algo ajeno.
- **Hay un paso de configuración más, y no es opcional.** Sacar un token de
  Lichess es un minuto y es gratis (RNF-1 pide que no haya servicios de pago,
  no que no haya cuentas), pero es una barrera real: sin él, esta pantalla no
  puede traer nada. Por eso la interfaz distingue "falta el token" de "el
  servicio no responde": lo primero tiene arreglo y lo dice, con el enlace
  donde se saca.

## Alternativas descartadas

- **Usar la tabla ECO que ya está versionada** (ADR-0009). Es la alternativa
  que primero se piensa —está offline, está a mano y va de aperturas—, y no
  vale: dice si una posición **tiene nombre**, no con qué frecuencia la juegan
  los maestros ni con qué resultado. Con ella se puede responder "esto ya no es
  una apertura conocida", que no es la pregunta: RF-3.6 pide "dónde me salgo de
  la línea principal **y con qué resultado**". Además tiene huecos a propósito
  (solo nombra los finales de línea), así que confundiría un hueco con una
  salida del repertorio.
- **Descargar una base de maestros al instalar.** Es lo que se hizo con la tabla
  ECO (ADR-0009), pero aquí no cabe: las bases de partidas de maestros
  utilizables pesan gigabytes y su licencia no siempre permite redistribuirlas.
- **Consultar en cada carga de la pantalla, sin caché.** Sería una petición por
  posición y por visita: lento para el usuario y abusivo para Lichess (RNF-10).
- **Precalcular al sincronizar.** Mezclaría dos servicios ajenos en la misma
  operación y haría que importar partidas dependiera de que Lichess responda.
  Importar seguiría siendo lo que RNF-1 llama "la importación inicial", pero
  fallaría por algo que no tiene que ver con chess.com.
- **Usar la base de partidas de Lichess en vez de la de maestros.** Responde a
  otra pregunta: qué juega todo el mundo, no qué es teoría. La comparación de
  RF-3.6 es contra la línea principal.

## Qué no fija

Ni cuántas jugadas se comparan ni qué cuenta como repertorio (hoy, cinco
partidas de maestros): son umbrales con nombre en
`lucia_api.services.repertoire`, ajustables sin tocar esta decisión. Tampoco
fija que la caché no caduque nunca; hoy no caduca porque la teoría cambia
despacio, y `fetched_at` está guardado por si algún día conviene.
