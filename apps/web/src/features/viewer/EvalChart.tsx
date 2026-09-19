/** Gráfico de evaluación de la partida (RF-5.1).
 *
 * El eje Y es probabilidad de victoria de las blancas (0-100), no
 * centipawns: una ventaja de +300 y otra de +900 están igual de ganadas en
 * la práctica, y en centipawns el gráfico se dispara y aplasta el resto.
 *
 * Cada punto se pinta del color de su clasificación (RF-2.2), y los errores
 * salen más grandes: así el gráfico enseña *dónde* se torció la partida, que
 * es lo que se viene a buscar, y no solo la curva. El color no va solo —el
 * texto emergente nombra la clasificación— porque el color por sí mismo no
 * puede cargar con el significado (criterio C-7 de docs/07-coherencia-ui.md).
 */
import type { AnalyzedMoveOut } from "@lucia/shared-types";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { classificationStyle, MISTAKE_CLASSIFICATIONS } from "../../lib/classification";
import { useChartTheme } from "../../lib/chartTheme";
import { formatPercent } from "../../lib/format";
import { moveNumberLabel, moveNumberOf } from "../../lib/moves";
import { whiteWinPercentAfterMove } from "../../lib/score";

interface EvalChartProps {
  moves: AnalyzedMoveOut[];
  currentPly: number;
  /** Ply de la posición de partida, para numerar como el resto de la pantalla. */
  startingPly: number;
  onSelectPly: (ply: number) => void;
}

export function EvalChart({ moves, currentPly, startingPly, onSelectPly }: EvalChartProps) {
  const theme = useChartTheme();
  const data = moves.map((move) => ({
    ply: move.ply,
    whiteWinPercent: whiteWinPercentAfterMove(move),
    san: move.san,
    classification: move.classification,
  }));

  return (
    <figure className="space-y-1">
      {/* El eje iba de 0 a 100 sin decir de qué: había que señalar un punto
          con el ratón para averiguarlo. */}
      <figcaption className="text-xs opacity-60">
        Probabilidad de victoria de las blancas, jugada a jugada
      </figcaption>
      <div className="h-40 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 5, right: 5, bottom: 5, left: 0 }}
            onClick={(state) => {
              const ply = state?.activePayload?.[0]?.payload?.ply;
              if (typeof ply === "number") onSelectPly(ply);
            }}
          >
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis
              dataKey="ply"
              tick={theme.axisTickStyle}
              stroke={theme.axisColor}
              // El eje enseña el número de jugada de la partida, el mismo que
              // la lista y la comparación de motores.
              tickFormatter={(ply) => String(moveNumberOf(Number(ply) + startingPly))}
            />
            <YAxis
              domain={[0, 100]}
              tick={theme.axisTickStyle}
              stroke={theme.axisColor}
              width={32}
              unit="%"
            />
            <ReferenceLine y={50} strokeDasharray="4 4" className="opacity-60" />
            <ReferenceLine x={currentPly} stroke={theme.seriesColor} strokeWidth={2} />
            <Tooltip
              contentStyle={theme.tooltipStyle}
              labelFormatter={(ply) => `Jugada ${moveNumberLabel(Number(ply) + startingPly)}`}
              formatter={(value: number, _name, entry) => [
                `${formatPercent(value, 1)} blancas · ${entry.payload.san} (${classificationStyle(entry.payload.classification).label})`,
                "Prob. de victoria",
              ]}
            />
            <Area
              type="monotone"
              dataKey="whiteWinPercent"
              stroke={theme.seriesColor}
              fill={theme.seriesColor}
              fillOpacity={0.25}
              isAnimationActive={false}
              dot={<ClassificationDot />}
              activeDot={{ r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}

/** Punto de una jugada, del color de su clasificación. Los errores se dibujan
 * más grandes; el resto, discretos, para que la curva siga leyéndose. */
function ClassificationDot(props: {
  cx?: number;
  cy?: number;
  payload?: { classification: string };
}) {
  const { cx, cy, payload } = props;
  if (cx === undefined || cy === undefined || !payload) return null;
  const isMistake = MISTAKE_CLASSIFICATIONS.includes(payload.classification);
  return (
    <circle
      cx={cx}
      cy={cy}
      r={isMistake ? 4 : 1.5}
      fill={classificationStyle(payload.classification).color}
    />
  );
}
