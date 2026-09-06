/** Dashboard de estadísticas (RF-3.1 a RF-3.3).
 *
 * Todo se calcula en la API sobre lo ya guardado; aquí solo se presenta. Las
 * secciones que dependen de un análisis terminado avisan cuando no hay
 * ninguno, en vez de mostrar ceros que parecerían un rendimiento pésimo.
 */
import type { PhaseStats, PlayerStats, RecordSummary } from "@lucia/shared-types";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
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
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { api } from "../../lib/api";
import { formatAccuracy } from "../../lib/format";

const PHASE_LABELS: Record<string, string> = {
  opening: "Apertura",
  middlegame: "Medio juego",
  endgame: "Final",
};

export function DashboardPage() {
  const [username, setUsername] = useState("");
  const [applied, setApplied] = useState<string | undefined>(undefined);

  const statsQuery = useQuery({
    queryKey: ["stats", applied],
    queryFn: () => api.getStats(applied),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-2xl font-bold">Estadísticas</h1>
        <form
          className="flex items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            setApplied(username || undefined);
          }}
        >
          <label className="text-sm">
            <span className="mb-1 block opacity-70">Jugador</span>
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="el de .env"
              className="w-52 rounded border border-slate-300 bg-white px-2 py-1.5 dark:border-slate-700 dark:bg-slate-900"
            />
          </label>
          <button
            type="submit"
            className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
          >
            Ver
          </button>
        </form>
      </div>

      {statsQuery.isPending && <Spinner />}
      {statsQuery.isError && <ErrorBox error={statsQuery.error} onRetry={statsQuery.refetch} />}
      {statsQuery.data && <StatsContent stats={statsQuery.data} />}
    </div>
  );
}

function StatsContent({ stats }: { stats: PlayerStats }) {
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
        <StatCard label="Puntuación" value={`${stats.overall.score_percent.toFixed(1)}%`} />
        <StatCard label="Analizadas" value={String(stats.analyzed_games)} />
        <StatCard label="Precisión media" value={formatAccuracy(stats.average_accuracy)} />
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Por control de tiempo</h2>
        <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2 font-medium">Control</th>
                <th className="px-3 py-2 font-medium">Rating</th>
                <th className="px-3 py-2 font-medium">V/T/D</th>
                <th className="px-3 py-2 font-medium">Puntuación</th>
                <th className="px-3 py-2 font-medium">Partidas</th>
              </tr>
            </thead>
            <tbody>
              {stats.by_time_class.map((item) => (
                <tr key={item.time_class} className="border-t border-slate-200 dark:border-slate-800">
                  <td className="px-3 py-2 capitalize">{item.time_class}</td>
                  <td className="px-3 py-2 tabular-nums">{item.current_rating ?? "—"}</td>
                  <td className="px-3 py-2">
                    <RecordBadges record={item.record} />
                  </td>
                  <td className="px-3 py-2 tabular-nums">
                    {item.record.score_percent.toFixed(1)}%
                  </td>
                  <td className="px-3 py-2 tabular-nums opacity-70">{item.record.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Partidas por mes</h2>
        <div className="h-48 rounded border border-slate-200 p-2 dark:border-slate-800">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={stats.by_month.map((m) => ({
                label: `${m.year}-${String(m.month).padStart(2, "0")}`,
                games: m.games,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="games" fill="#6366f1" isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
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
          <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2 font-medium">Apertura</th>
                  <th className="px-3 py-2 font-medium">Color</th>
                  <th className="px-3 py-2 font-medium">V/T/D</th>
                  <th className="px-3 py-2 font-medium">Puntuación</th>
                  <th className="px-3 py-2 font-medium">Precisión</th>
                </tr>
              </thead>
              <tbody>
                {stats.by_opening.map((item) => (
                  <tr
                    key={`${item.opening}-${item.color}`}
                    className="border-t border-slate-200 dark:border-slate-800"
                  >
                    <td className="px-3 py-2">{item.opening}</td>
                    <td className="px-3 py-2 opacity-70">
                      {item.color === "white" ? "Blancas" : "Negras"}
                    </td>
                    <td className="px-3 py-2">
                      <RecordBadges record={item.record} />
                    </td>
                    <td className="px-3 py-2 tabular-nums">
                      {item.record.score_percent.toFixed(1)}%
                    </td>
                    <td className="px-3 py-2 tabular-nums opacity-70">
                      {formatAccuracy(item.average_accuracy)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function PhaseSection({ phases }: { phases: PhaseStats[] }) {
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
      <div className="h-48 rounded border border-slate-200 p-2 dark:border-slate-800">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} width={36} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(value: number) => [`${value}%`, "Prob. de victoria perdida por jugada"]}
            />
            <Bar dataKey="lost" isAnimationActive={false}>
              {data.map((entry) => (
                <Cell key={entry.label} fill={entry.label === worst.label ? "#ef4444" : "#6366f1"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ul className="space-y-2 text-sm">
        {data.map((phase) => (
          <li
            key={phase.label}
            className="rounded border border-slate-200 p-2 dark:border-slate-800"
          >
            <div className="flex justify-between font-medium">
              <span>{phase.label}</span>
              <span className="tabular-nums">{phase.accuracy.toFixed(1)}</span>
            </div>
            <p className="mt-0.5 text-xs opacity-60">
              {phase.moves} jugadas · {phase.blunders} blunders · pierde {phase.lost}% por jugada
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs uppercase tracking-wide opacity-60">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function RecordBadges({ record }: { record: RecordSummary }) {
  return (
    <span className="flex gap-1 text-xs">
      <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200">
        {record.wins}
      </span>
      <span className="rounded bg-slate-200 px-1.5 py-0.5 text-slate-700 dark:bg-slate-700 dark:text-slate-200">
        {record.draws}
      </span>
      <span className="rounded bg-red-100 px-1.5 py-0.5 text-red-800 dark:bg-red-900/60 dark:text-red-200">
        {record.losses}
      </span>
    </span>
  );
}
