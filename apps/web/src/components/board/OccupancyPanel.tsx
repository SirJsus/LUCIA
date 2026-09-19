/** El panel que gobierna y explica la capa de ocupación (RF-7).
 *
 * Va **bajo** el tablero en las dos pantallas que lo tienen —el visor (RF-5) y
 * el tablero de análisis (RF-6)—, en el mismo sitio y con los mismos nombres,
 * porque la capa es la misma (criterio C-2 de docs/07-coherencia-ui.md). Bajo
 * el tablero y no en el lateral con los demás paneles porque este es la leyenda
 * de lo que se está pintando encima de él, y leer "borde a rayas ámbar" a dos
 * columnas de la casilla que lo lleva obliga a cruzar la vista (fila 90 del
 * inventario). Tiene tres trabajos:
 *
 * - **Encenderla y configurarla**: el sub-modo (RF-7.1 y RF-7.2), qué bando se
 *   mira y qué marcas se enseñan. El botón de encendido está siempre, también
 *   apagada: un control que solo aparece cuando ya se usa no se descubre nunca
 *   (criterio C-3, la misma razón de la fila 68 del inventario).
 * - **Inspeccionar una casilla** (RF-7.3): quién la ataca y quién la defiende,
 *   de la pieza más valiosa a la menos.
 * - **Ser la leyenda** de lo que se ve sobre el tablero: qué significa cada
 *   color, cada borde y cada línea, en palabras (criterios C-6 y C-7).
 */
import { Button } from "../Button";
import { EmptyState, ErrorBox } from "../Feedback";
import { Panel } from "../Panel";
import { sortAttacksByValue, type Attack, type OccupancyMap } from "./occupancy";
import { colorName, otherColor, pieceName, type PieceColor } from "./pieces";
import type { OccupancyController, OccupancyMark } from "./useOccupancy";

/** Las tres marcas, con lo que sale al encenderlas. La ayuda va aquí y no en la
 * leyenda porque hay que poder saber qué se va a ver **antes** de marcarla
 * (fila 89 del inventario de docs/07-coherencia-ui.md). */
const MARK_CONTROLS: { mark: OccupancyMark; label: string; hint: string }[] = [
  {
    mark: "hanging",
    label: "Piezas colgadas",
    hint: "Rodea las piezas atacadas que nadie defiende, o que ataca una pieza de menor valor.",
  },
  {
    mark: "pinned",
    label: "Piezas clavadas",
    hint: "Rodea las piezas que no pueden moverse porque dejarían a su rey en jaque.",
  },
  {
    mark: "xray",
    label: "Rayos X",
    hint:
      "Dibuja con línea discontinua el alcance a través de otra pieza: una torre tras otra, o " +
      "una dama que llega al rey por detrás de un caballo. Nunca cuenta en el balance.",
  },
];

export function OccupancyPanel({ controller }: { controller: OccupancyController }) {
  const {
    isActive,
    toggle,
    occupancy,
    mode,
    setMode,
    coverageColor,
    isShowingOtherColor,
    toggleCoverageColor,
    marks,
    toggleMark,
    selectedSquare,
  } = controller;

  return (
    <Panel
      title="Ocupación del tablero"
      aside={
        <Button size="sm" onClick={toggle}>
          {isActive ? "Apagar" : "Encender"}
        </Button>
      }
      bodyClassName="space-y-3 p-3 text-sm"
    >
      {!isActive ? (
        <p className="opacity-70">
          Colorea cada casilla según quién la controla, marca las piezas colgadas y las
          clavadas, y dice quién ataca y quién defiende la casilla que pulses. Se enciende aquí
          o con la tecla{" "}
          <kbd className="rounded border border-slate-300 px-1 font-mono text-xs dark:border-slate-700">
            O
          </kbd>
          .
        </p>
      ) : !occupancy ? (
        // Encendida y sin mapa es que el FEN de la posición no se ha podido
        // leer. Antes caía en la rama de arriba y la capa se anunciaba como
        // apagada teniendo el botón en "Apagar" (criterios C-3 y C-4).
        <ErrorBox
          error={
            "No se ha podido leer la posición que hay en el tablero, " +
            "así que no hay ocupación que enseñar."
          }
        />
      ) : (
        <>
          <fieldset>
            <legend className="opacity-70">Qué se enseña</legend>
            <div className="mt-1 space-y-1">
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  name="occupancy-mode"
                  checked={mode === "heatmap"}
                  onChange={() => setMode("heatmap")}
                />
                Mapa de calor: quién domina cada casilla
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  name="occupancy-mode"
                  checked={mode === "coverage"}
                  onChange={() => setMode("coverage")}
                />
                Cobertura directa: hasta dónde llega un bando
              </label>
            </div>
          </fieldset>

          {mode === "coverage" && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="opacity-70">
                Se ven las {colorName(coverageColor)}
                {isShowingOtherColor ? "" : ", que son las que mueven"}.
              </span>
              <Button size="sm" onClick={toggleCoverageColor}>
                Ver las {colorName(otherColor(coverageColor))}
              </Button>
            </div>
          )}

          <fieldset>
            <legend className="opacity-70">Qué se marca</legend>
            <div className="mt-1 space-y-2">
              {MARK_CONTROLS.map(({ mark, label, hint }) => (
                <div key={mark}>
                  <label className="flex items-center gap-1.5">
                    <input
                      type="checkbox"
                      checked={marks[mark]}
                      onChange={() => toggleMark(mark)}
                    />
                    {label}
                  </label>
                  {/* Qué sale al marcarla, a la vista y no en un `title`: con
                      teclado un `title` no aparece nunca, y la leyenda de abajo
                      solo explica lo que ya está encendido (criterio C-6, la
                      misma razón que bajó las ayudas de los filtros de
                      Partidas bajo su campo). */}
                  <p className="ml-5 text-xs opacity-60">{hint}</p>
                </div>
              ))}
            </div>
          </fieldset>

          {selectedSquare ? (
            <SquareInspection occupancy={occupancy} square={selectedSquare} />
          ) : (
            <EmptyState title="Ninguna casilla elegida">
              Pulsa una casilla del tablero para ver quién la ataca y quién la defiende. Señala una
              pieza para ver solo lo que cubre.
            </EmptyState>
          )}

          <OccupancyLegend
            mode={mode}
            coverageColor={coverageColor}
            marks={marks}
          />
        </>
      )}
    </Panel>
  );
}

/** Quién ataca y quién defiende una casilla (RF-7.3).
 *
 * Los dos bandos van siempre, y en cada uno las piezas van de la más valiosa a
 * la menos. Si la casilla tiene pieza, se nombra a los bandos por lo que hacen
 * —atacar o defender—, que es como se habla de una posición; si está vacía, los
 * dos bandos la cubren y no hay nada que defender.
 */
function SquareInspection({ occupancy, square }: { occupancy: OccupancyMap; square: string }) {
  const piece = occupancy.pieces[square];
  const { directAttacks, xrayAttacks } = occupancy.squares[square];
  const sides: PieceColor[] = piece ? [otherColor(piece.color), piece.color] : ["w", "b"];

  return (
    <div className="space-y-2 border-t border-slate-200 pt-2 dark:border-slate-800">
      <p className="font-medium">
        <span className="font-mono">{square}</span>
        {piece ? `: ${pieceName(piece.role, piece.color)}` : ": casilla vacía"}
        {piece && occupancy.pinnedSquares.includes(square) && (
          <span className="ml-1 text-amber-700 dark:text-amber-400">· clavada contra su rey</span>
        )}
        {piece && occupancy.hangingSquares.includes(square) && (
          <span className="ml-1 text-red-700 dark:text-red-400">· colgada</span>
        )}
      </p>

      {sides.map((color) => (
        <AttackList
          key={color}
          heading={
            piece
              ? color === piece.color
                ? `Defienden las ${colorName(color)}`
                : `Atacan las ${colorName(color)}`
              : `Cubren las ${colorName(color)}`
          }
          directAttacks={directAttacks[color]}
          xrayAttacks={xrayAttacks[color]}
        />
      ))}
    </div>
  );
}

function AttackList({
  heading,
  directAttacks,
  xrayAttacks,
}: {
  heading: string;
  directAttacks: Attack[];
  xrayAttacks: Attack[];
}) {
  return (
    <div>
      <p className="text-xs opacity-70">
        {heading} ({directAttacks.length})
      </p>
      {directAttacks.length === 0 ? (
        <p className="text-xs opacity-50">Nadie.</p>
      ) : (
        <ul className="mt-0.5 space-y-0.5">
          {sortAttacksByValue(directAttacks).map((attack) => (
            <li key={attack.from}>
              {pieceName(attack.role, attack.color)} de{" "}
              <span className="font-mono">{attack.from}</span>
              {/* La clavada se dice, además de marcarse en el tablero: sigue
                  contando como atacante y conviene saber por qué está ahí
                  (RF-7.6). */}
              {attack.isPinned && (
                <span className="opacity-70"> · clavada, no puede moverse</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {xrayAttacks.length > 0 && (
        <ul className="mt-0.5 space-y-0.5 opacity-70">
          {sortAttacksByValue(xrayAttacks).map((attack) => (
            <li key={attack.from} className="text-xs">
              {pieceName(attack.role, attack.color)} de{" "}
              <span className="font-mono">{attack.from}</span>, por rayo X a través de{" "}
              <span className="font-mono">{attack.throughSquare}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Qué significa cada cosa que se ve sobre el tablero. Sin esto, la capa es un
 * cuadro de colores: el número, el borde y la línea discontinua solo informan
 * si se dice qué son (criterios C-6 y C-7). */
function OccupancyLegend({
  mode,
  coverageColor,
  marks,
}: {
  mode: OccupancyController["mode"];
  coverageColor: PieceColor;
  /** Las dos marcas que se pueden apagar solo se explican cuando están
   * encendidas: una leyenda que nombra lo que no está en pantalla se lee como
   * si faltara algo (criterio C-6). */
  marks: OccupancyController["marks"];
}) {
  const entries: [swatch: string, text: string][] =
    mode === "heatmap"
      ? [
          ["bg-sky-500/40", "Dominan las blancas; el número dice por cuántas piezas de más."],
          ["bg-orange-600/40", "Dominan las negras."],
          ["bg-slate-500/30", "Disputada: los dos bandos llegan con las mismas piezas («=»)."],
          [
            "border border-dashed border-slate-400 dark:border-slate-500",
            "Sin control: no la alcanza nadie.",
          ],
        ]
      : [
          [
            coverageColor === "w" ? "bg-sky-500/40" : "bg-orange-600/40",
            `Casillas que cubren las ${colorName(coverageColor)}; el número dice con cuántas piezas.`,
          ],
        ];

  return (
    <ul className="space-y-1 border-t border-slate-200 pt-2 text-xs opacity-70 dark:border-slate-800">
      {entries.map(([swatch, text]) => (
        <li key={text} className="flex items-start gap-2">
          <span className={`mt-0.5 size-3 shrink-0 rounded-sm ${swatch}`} aria-hidden="true" />
          {text}
        </li>
      ))}
      {marks.hanging && (
        <li className="flex items-start gap-2">
          <span
            className="mt-0.5 size-3 shrink-0 rounded-sm border-2 border-red-600"
            aria-hidden="true"
          />
          Borde continuo rojo: pieza colgada, atacada sin defensa o por una de menor valor.
        </li>
      )}
      {marks.pinned && (
        <li className="flex items-start gap-2">
          <span
            className="mt-0.5 size-3 shrink-0 rounded-sm border-2 border-dashed border-amber-500"
            aria-hidden="true"
          />
          Borde a rayas ámbar: pieza clavada contra su rey. Sigue contando como atacante, pero no
          puede moverse.
        </li>
      )}
      {marks.xray && (
        <li className="flex items-start gap-2">
          <span
            className="mt-1.5 h-0 w-3 shrink-0 border-t-2 border-dashed border-slate-500"
            aria-hidden="true"
          />
          Línea discontinua: rayo X, el alcance a través de otra pieza. Nunca cuenta en el
          balance.
        </li>
      )}
    </ul>
  );
}
