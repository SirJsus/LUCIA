/** Dashboard de estadísticas (RF-3.1 a RF-3.3).
 *
 * Todo se calcula en la API sobre lo ya guardado; aquí solo se presenta. Las
 * secciones que dependen de un análisis terminado avisan cuando no hay
 * ninguno, en vez de mostrar ceros que parecerían un rendimiento pésimo.
 */
import type { PhaseStats, PlayerStats, RecordSummary } from "@lucia/shared-types";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge, type BadgeTone } from "../../components/Badge";
import { DataTable } from "../../components/DataTable";
import { Panel } from "../../components/Panel";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import {
  FIELD_CLASSES,
  PANEL_CLASSES,
  TABLE_CELL_CLASSES,
  TABLE_ROW_CLASSES,
} from "../../components/styles";
import { api } from "../../lib/api";
import { useChartTheme } from "../../lib/chartTheme";
import {
  formatAccuracy,
  formatPercent,
  formatTimeClass,
  formatYearMonth,
} from "../../lib/format";

/** El encabezado de la columna de marcador, en las dos tablas que lo tienen:
 * la abreviatura sola no se entiende sin desarrollarla (criterio C-6). */
const RECORD_HEADER = <abbr title="Victorias / Tablas / Derrotas">V/T/D</abbr>;

const PHASE_LABELS: Record<string, string> = {
  opening: "Apertura",
  middlegame: "Medio juego",
  endgame: "Final",
};

/** Espera antes de consultar con el nombre tecleado. En Partidas el filtro se
 * aplica al escribir y aquí hacía falta pulsar un botón "Ver": la misma acción
 * funcionaba de dos maneras según la pantalla (criterio C-2 de
 * docs/07-coherencia-ui.md). El retardo evita una consulta por tecla, que es
 * lo que el botón estaba resolviendo a mano. */
const FILTER_DELAY_MS = 400;

export function DashboardPage() {
  const [username, setUsername] = useState("");
  const [appliedUsername, setAppliedUsername] = useState<string | undefined>(undefined);

  useEffect(() => {
    const timer = setTimeout(() => setAppliedUsername(username || undefined), FILTER_DELAY_MS);
    return () => clearTimeout(timer);
  }, [username]);

  const statsQuery = useQuery({
    queryKey: ["stats", appliedUsername],
    queryFn: () => api.getStats(appliedUsername),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Estadísticas</h1>

      {/* La barra de filtros va bajo el título y con la misma forma que la de
          Partidas: era el mismo filtro en dos sitios distintos (criterio C-2
          de docs/07-coherencia-ui.md). */}
      <div className={`flex flex-wrap gap-3 p-3 text-sm ${PANEL_CLASSES}`}>
        <label className="flex flex-col gap-1">
          <span className="opacity-70">Jugador</span>
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="el de .env"
            className={`w-52 ${FIELD_CLASSES}`}
          />
        </label>
      </div>

      {statsQuery.isPending && <Spinner />}
      {statsQuery.isError && <ErrorBox error={statsQuery.error} onRetry={statsQuery.refetch} />}
      {statsQuery.data && <StatsContent stats={statsQuery.data} />}
    </div>
  );
}

function StatsContent({ stats }: { stats: PlayerStats }) {
  const theme = useChartTheme();

  if (stats.total_games === 0) {
    return (
      <EmptyState title={`Sin partidas de "${stats.username}"`}>
        Sincroniza ese usuario desde la pantalla de Partidas, o comprueba que el nombre coincide con
        el de chess.com.
      </EmptyState>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Partidas" value={String(stats.total_games)} />
        <StatCard label="Puntuación" value={formatPercent(stats.overall.score_percent, 1)} />
        <StatCard label="Analizadas" value={String(stats.analyzed_games)} />
        <StatCard label="Precisión media" value={formatAccuracy(stats.average_accuracy)} />
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Por control de tiempo</h2>
        <DataTable headers={["Control", "Rating", RECORD_HEADER, "Puntuación", "Partidas"]}>
          {stats.by_time_class.map((item) => (
            <tr key={item.time_class} className={TABLE_ROW_CLASSES}>
              <td className={TABLE_CELL_CLASSES}>{formatTimeClass(item.time_class)}</td>
              <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>{item.current_rating ?? "—"}</td>
              <td className={TABLE_CELL_CLASSES}>
                <RecordBadges record={item.record} />
              </td>
              <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>
                {formatPercent(item.record.score_percent, 1)}
              </td>
              <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
                {item.record.total}
              </td>
            </tr>
          ))}
        </DataTable>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Partidas por mes</h2>
        <Panel bodyClassName="h-48 p-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={stats.by_month.map((month) => ({
                label: formatYearMonth(month.year, month.month),
                games: month.games,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: theme.axisColor }} stroke={theme.axisColor} />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11, fill: theme.axisColor }}
                stroke={theme.axisColor}
                width={32}
              />
              <Tooltip contentStyle={theme.tooltipStyle} formatter={(value: number) => [value, "Partidas"]} />
              <Bar dataKey="games" fill={theme.seriesColor} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Por fase de la partida</h2>
        {stats.by_phase.length === 0 ? (
          <EmptyState title="Aún no hay análisis">
            Analiza alguna partida desde su visor para ver en qué fase se pierde más ventaja.
          </EmptyState>
        ) : (
          <PhaseSection phases={stats.by_phase} />
        )}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Por apertura</h2>
        {stats.by_opening.length === 0 ? (
          <EmptyState title="Sin datos de apertura">
            chess.com no reportó la apertura de estas partidas.
          </EmptyState>
        ) : (
          <DataTable headers={["Apertura", "Color", RECORD_HEADER, "Puntuación", "Precisión"]}>
            {stats.by_opening.map((item) => (
              <tr key={`${item.opening}-${item.color}`} className={TABLE_ROW_CLASSES}>
                <td className={TABLE_CELL_CLASSES}>{item.opening}</td>
                <td className={`opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {item.color === "white" ? "Blancas" : "Negras"}
                </td>
                <td className={TABLE_CELL_CLASSES}>
                  <RecordBadges record={item.record} />
                </td>
                <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>
                  {formatPercent(item.record.score_percent, 1)}
                </td>
                <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {formatAccuracy(item.average_accuracy)}
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </section>
    </div>
  );
}

function PhaseSection({ phases }: { phases: PhaseStats[] }) {
  const theme = useChartTheme();
  const data = phases.map((phase) => ({
    label: PHASE_LABELS[phase.phase] ?? phase.phase,
    lost: Number(phase.average_win_percent_lost.toFixed(2)),
    accuracy: phase.average_accuracy,
    moves: phase.moves,
    blunders: phase.blunders,
  }));
  // La fase con más pérdida media es la que hay que entrenar: se resalta.
  const worst = data.reduce((a, b) => (b.lost > a.lost ? b : a), data[0]);

  return (
    <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="space-y-1">
        <Panel bodyClassName="h-48 p-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: theme.axisColor }} stroke={theme.axisColor} />
              <YAxis
                tick={{ fontSize: 11, fill: theme.axisColor }}
                stroke={theme.axisColor}
                width={36}
                unit="%"
              />
              <Tooltip
                contentStyle={theme.tooltipStyle}
                formatter={(value: number) => [
                  formatPercent(value, 2),
                  "Prob. de victoria perdida por jugada",
                ]}
              />
              <Bar dataKey="lost" isAnimationActive={false}>
                {data.map((entry) => (
                  <Cell
                    key={entry.label}
                    fill={entry.label === worst.label ? theme.highlightColor : theme.seriesColor}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        {/* La barra destacada se explicaba sola con el color, que no dice qué
            significa ni sirve a quien no lo distingue (criterio C-7). */}
        <p className="text-xs opacity-60">
          Probabilidad de victoria que se pierde por jugada en cada fase. Destacada, la fase donde
          más se pierde: {worst.label}.
        </p>
      </div>

      <ul className="space-y-2 text-sm">
        {data.map((phase) => (
          <li key={phase.label} className={`p-2 ${PANEL_CLASSES}`}>
            <div className="flex justify-between font-medium">
              <span>
                {phase.label}
                {phase.label === worst.label && (
                  <span className="ml-1.5 font-normal">
                    <Badge tone="danger">la que más cuesta</Badge>
                  </span>
                )}
              </span>
              <span className="tabular-nums">{formatAccuracy(phase.accuracy)}</span>
            </div>
            <p className="mt-0.5 text-xs opacity-60">
              {phase.moves} jugadas · {phase.blunders} blunders · pierde {formatPercent(phase.lost, 2)} por
              jugada
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Panel>
      <p className="text-xs uppercase tracking-wide opacity-60">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
    </Panel>
  );
}

/** Victorias, tablas y derrotas. Cada número lleva su letra: los tres se
 * distinguían solo por el color de fondo, que no es una diferencia para quien
 * no los ve (criterio C-7 de docs/07-coherencia-ui.md). */
function RecordBadges({ record }: { record: RecordSummary }) {
  return (
    <span className="flex gap-1">
      <RecordBadge count={record.wins} letter="V" name="victorias" tone="success" />
      <RecordBadge count={record.draws} letter="T" name="tablas" tone="neutral" />
      <RecordBadge count={record.losses} letter="D" name="derrotas" tone="danger" />
    </span>
  );
}

function RecordBadge({
  count,
  letter,
  name,
  tone,
}: {
  count: number;
  letter: string;
  name: string;
  tone: BadgeTone;
}) {
  return (
    <Badge tone={tone} title={`${count} ${name}`}>
      <span className="tabular-nums">{count}</span> {letter}
    </Badge>
  );
}
