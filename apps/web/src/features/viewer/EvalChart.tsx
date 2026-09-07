/** Gráfico de evaluación de la partida (RF-5.1).
 *
 * El eje Y es probabilidad de victoria de las blancas (0-100), no
 * centipawns: una ventaja de +300 y otra de +900 están igual de ganadas en
 * la práctica, y en centipawns el gráfico se dispara y aplasta el resto.
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
import { classificationStyle } from "../../lib/classification";
import { whiteWinPercentAfterMove } from "../../lib/score";

interface EvalChartProps {
  moves: AnalyzedMoveOut[];
  currentPly: number;
  onSelectPly: (ply: number) => void;
}

export function EvalChart({ moves, currentPly, onSelectPly }: EvalChartProps) {
  const data = moves.map((move) => ({
    ply: move.ply,
    whiteWinPercent: whiteWinPercentAfterMove(move),
    san: move.san,
    classification: move.classification,
  }));

  return (
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
          <XAxis dataKey="ply" tick={{ fontSize: 11 }} tickFormatter={(ply) => String(ply + 1)} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} width={32} />
          <ReferenceLine y={50} strokeDasharray="4 4" className="opacity-60" />
          <ReferenceLine x={currentPly} stroke="#6366f1" strokeWidth={2} />
          <Tooltip
            contentStyle={{ fontSize: 12 }}
            labelFormatter={(ply) => `Jugada ${Number(ply) + 1}`}
            formatter={(value: number, _name, entry) => [
              `${value.toFixed(1)}% blancas · ${entry.payload.san} (${classificationStyle(entry.payload.classification).label})`,
              "Prob. de victoria",
            ]}
          />
          <Area
            type="monotone"
            dataKey="whiteWinPercent"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.25}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
