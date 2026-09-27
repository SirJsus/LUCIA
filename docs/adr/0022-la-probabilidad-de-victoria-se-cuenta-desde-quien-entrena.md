# ADR-0022 · La probabilidad de victoria se cuenta desde quien entrena cuando la frase nombra el bando

**Estado:** aceptado · **Fecha:** 2026-09-22

## Contexto

El criterio **C-5** de [07-coherencia-ui.md](../07-coherencia-ui.md) ("un dato,
una forma") dice que la evaluación se presenta igual en todas partes: mismo
signo, misma unidad, mismo formateador y **mismo punto de vista, el de las
blancas**. No es un capricho de estilo: la barra de evaluación, el gráfico de
la partida y las columnas del dashboard enseñan la misma cifra, y un punto de
vista que cambia de pantalla en pantalla convierte "+31" en un número que no se
puede leer sin saber quién lo escribió. La fila **52** del inventario se cerró
en su día precisamente por eso, girando a blancas un porcentaje que se contaba
desde el otro lado.

Las pantallas de entrenamiento (RF-4) trajeron un caso que ese criterio no
había visto. Cuando lo que se enseña es **el error propio** —el puzzle resuelto
de RF-4.1 y la lista de re-jugar de RF-4.4—, la cifra no aparece suelta en una
columna: aparece dentro de una frase que ya dice de quién habla, "Tu
probabilidad de victoria pasó de 62,0 % a 31,0 %". Aplicar C-5 al pie de la
letra obliga a girarla a las blancas, y entonces quien juega con negras lee
**"31 puntos más"** justo debajo del titular que le dice que acaba de cometer
un error grave. La frase y el número dicen lo contrario.

Es la fila **92** del inventario, abierta el 2026-09-19 con la pantalla de
puzzles y dejada explícitamente sin cerrar —"mientras se decide, al menos el
punto de vista es uno solo"— hasta tener delante las seis pantallas de
Entrenamiento. Se decidió en el barrido de cierre de la fase 3, el 2026-09-22.

Las opciones eran tres:

1. **Girar a blancas** y ser coherente con la fila 52. Cuesta que la mitad de
   las veces la pérdida se lea como ganancia, y obliga a redactar la frase sin
   "menos", que es lo que la hace entendible.
2. **Reescribir la frase sin bando** ("La evaluación pasó de… a…"), que quita
   el problema quitando lo que hace útil la pantalla: lo que se entrena es el
   error **propio**, y esconder de quién es el error lo vuelve una estadística.
3. **Escribir la excepción en el criterio** y acotarla para que no se extienda.

## Decisión

**Una frase puede contar la probabilidad de victoria desde el bando de quien
entrena, siempre que la frase nombre ese bando explícitamente. En todo número
suelto el punto de vista sigue siendo obligatoriamente el de las blancas.
Cuando chocan, es C-5 el que cede, no la frase.**

- **Dónde se aplica**: el panel del puzzle resuelto (RF-4.1) y la lista de
  errores desde los que re-jugar (RF-4.4), que son las dos pantallas donde lo
  que se enseña es el error propio. Las dos usan el mismo formateador,
  `lib/format.ts::formatOwnWinPercentLossSentence`, para que no haya dos
  redacciones de lo mismo.
- **Qué cuenta como "nombrar el bando"**: que el sujeto de la frase sea quien
  entrena — "**Tu** probabilidad de victoria…". No basta con que el contexto lo
  sugiera, ni con un `title`, ni con una leyenda al lado: tiene que leerse en
  la misma frase que el número.
- **Qué sigue prohibido**: el número suelto. Una columna de tabla, una insignia,
  un punto de un gráfico, una barra o un `aria-label` sin frase van siempre
  desde las blancas, porque ahí nadie puede preguntar desde dónde se cuenta.
  La fila 52 sigue cerrada con su criterio intacto.
- **La consecuencia se acepta a la vista**: el mismo error sale como 31 % en la
  lista de re-jugar y como 69 % en el visor al que lleva su enlace "Ver
  partida". Es el precio, y es menor que el de escribir "31 puntos más" delante
  de una equivocación propia.

La excepción quedó escrita en la tabla de criterios de
[07-coherencia-ui.md](../07-coherencia-ui.md) (fila C-5) y en el docstring de
`formatOwnWinPercentLossSentence`. Este ADR existe porque un criterio con
excepción es una **decisión** —el barrido lo marcó como tal— y no un arreglo:
una fila de tabla y un docstring cuentan qué se hace, pero no dejan constancia
de qué se descartó ni de dónde está la frontera, que es justamente lo que hace
falta la próxima vez que una pantalla quiera contar algo "desde el usuario".

## Consecuencias

- **La frontera es redactable y comprobable.** Al revisar una pantalla nueva la
  pregunta es una sola: ¿este número va dentro de una frase que nombra el
  bando? Si sí, puede ir desde quien entrena; si no, va desde las blancas. No
  hace falta juzgar si la pantalla es "de entrenamiento" o "de análisis".
- **C-5 deja de ser absoluto**, y eso invita a pedirle otras excepciones. La
  mitigación es que la excepción está acotada a una magnitud (probabilidad de
  victoria), a una forma (frase con sujeto) y a un formateador compartido:
  ampliarla exige tocar el criterio, que es un cambio visible, y no colarla en
  una pantalla.
- **El signo y la unidad no se tocan.** La excepción es solo sobre el **punto
  de vista**; el formato del porcentaje sigue saliendo del mismo
  `formatPercent`, y la conversión de centipeones a probabilidad sigue siendo
  la de [ADR-0006](0006-probabilidad-de-victoria-en-el-cliente.md).
- **Si algún día se revierte**, la vuelta es un solo cambio:
  `formatOwnWinPercentLossSentence` es el único sitio que compone esta frase.
  Revertirla pediría un ADR nuevo que reemplace a este, no editar este.

## Ver también

- Criterio **C-5** y fila **92** del inventario en
  [07-coherencia-ui.md](../07-coherencia-ui.md), con el detalle del barrido de
  cierre de la fase 3 (entrada del 2026-09-22) donde se decidió.
- [ADR-0006](0006-probabilidad-de-victoria-en-el-cliente.md): de dónde sale la
  probabilidad de victoria y por qué se calcula en el cliente. Este ADR no la
  toca; solo dice desde qué lado se lee cuando la frase lo permite.
- **RNF-11** en [02-requerimientos.md](../02-requerimientos.md), el
  requerimiento del que C-5 es un criterio verificable.
- `apps/web/src/lib/format.ts` (`formatOwnWinPercentLossSentence`), y sus dos
  usos: `features/training/PuzzleSolver.tsx` y
  `features/training/ReplaysPage.tsx`.
