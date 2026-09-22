/** Dashboard de estadísticas (RF-3.1 a RF-3.7).
 *
 * Todo se calcula en la API sobre lo ya guardado; aquí solo se presenta. Las
 * secciones que dependen de un análisis terminado avisan cuando no hay
 * ninguno, en vez de mostrar ceros que parecerían un rendimiento pésimo.
 */
import type {
  MistakeTypeStats,
  PhaseStats,
  PlayerStats,
  TimeBucketStats,
  TimeTrouble,
  Trends,
} from "@lucia/shared-types";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "../../components/Badge";
import { RecordBadges } from "../../components/RecordBadges";
import { DataTable } from "../../components/DataTable";
import { Panel } from "../../components/Panel";
import { RepertoireSection } from "./RepertoireSection";
import { EmptyState, ErrorBox, Spinner } from "../../components/Feedback";
import { FilterBar, FilterText } from "../../components/FilterBar";
import {
  PANEL_CLASSES,
  TABLE_CELL_CLASSES,
  TABLE_ROW_CLASSES,
} from "../../components/styles";
import { api } from "../../lib/api";
import { useChartTheme } from "../../lib/chartTheme";
import {
  formatAccuracy,
  formatPercent,
  formatPhase,
  formatPerHundredMoves,
  formatRating,
  formatTimeClass,
  formatYearMonth,
} from "../../lib/format";
import { formatTimeLeftBucket, formatTrendSentence, mistakeTypeStyle } from "../../lib/insights";

/** El encabezado de la columna de marcador, en las dos tablas que lo tienen:
 * la abreviatura sola no se entiende sin desarrollarla (criterio C-6). */
const RECORD_HEADER = <abbr title="Victorias / Tablas / Derrotas">V/T/D</abbr>;

/** El código de la apertura en la clasificación ECO, el que usan las bases de
 * datos de ajedrez. Va abreviado porque la columna es estrecha. */
const ECO_HEADER = <abbr title="Código de la Enciclopedia de Aperturas de Ajedrez">ECO</abbr>;

/** Con qué posición se sale de la apertura (RF-3.2). El encabezado lleva la
 * explicación porque el número no se entiende solo: es probabilidad de
 * victoria, no puntuación. */
const OPENING_EXIT_HEADER = (
  <abbr title="Tu probabilidad de victoria media al terminar la apertura">Al salir</abbr>
);

/** Las dos columnas de tasa de la tabla de tendencias (RF-3.7). "/ 100" sin
 * desarrollar no dice de qué son cien, y el número no se puede comparar con
 * el "Errores" en recuento de las otras dos tablas del panel: la explicación
 * va en el encabezado, como en las demás columnas que no se leen solas
 * (criterio C-6). */
const MISTAKE_RATE_HEADER = (
  <abbr title="Errores por cada cien jugadas tuyas, para poder comparar meses con distinto número de partidas">
    Errores / 100
  </abbr>
);

const BLUNDER_RATE_HEADER = (
  <abbr title="De esos errores, los graves, también por cada cien jugadas tuyas">
    De ellos, blunders / 100
  </abbr>
);

export function DashboardPage() {
  // La espera de "deja de teclear y consulto" la hace `FilterText`, que es la
  // misma en Partidas: aquí solo se guarda el nombre ya aplicado.
  const [username, setUsername] = useState("");

  const statsQuery = useQuery({
    queryKey: ["stats", username],
    queryFn: () => api.getStats(username || undefined),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Estadísticas</h1>

      {/* La barra de filtros va bajo el título y con la misma forma que la de
          Partidas: era el mismo filtro en dos sitios distintos (criterio C-2
          de docs/07-coherencia-ui.md). */}
      <FilterBar>
        <FilterText
          label="Jugador"
          value={username}
          onChange={setUsername}
          placeholder="el de .env"
          width="w-52"
        />
      </FilterBar>

      {statsQuery.isPending && <Spinner />}
      {statsQuery.isError && <ErrorBox error={statsQuery.error} onRetry={statsQuery.refetch} />}
      {statsQuery.data && <StatsContent stats={statsQuery.data} username={username} />}
    </div>
  );
}

function StatsContent({ stats, username }: { stats: PlayerStats; username: string }) {
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
              <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>
                {formatRating(item.current_rating)}
              </td>
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
              <XAxis dataKey="label" tick={theme.axisTickStyle} stroke={theme.axisColor} />
              <YAxis
                allowDecimals={false}
                tick={theme.axisTickStyle}
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
        <h2 className="font-semibold">Por qué fallas</h2>
        {stats.by_mistake_type.length === 0 ? (
          <EmptyState title="Aún no hay errores que repartir">
            Analiza alguna partida desde su visor para ver de qué tipo son tus errores.
          </EmptyState>
        ) : (
          <MistakeTypeSection mistakeTypes={stats.by_mistake_type} />
        )}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Cómo evolucionas</h2>
        {stats.trends.by_month.length === 0 ? (
          <EmptyState title="Aún no hay análisis que comparar">
            La evolución se calcula sobre las partidas analizadas: analiza algunas desde su visor
            para ver si mejoras.
          </EmptyState>
        ) : (
          <TrendsSection trends={stats.trends} />
        )}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Con el reloj en la mano</h2>
        {stats.by_time_left.length === 0 ? (
          <EmptyState title="Sin relojes que mirar">
            Solo las partidas de chess.com con reloj por jugada cuentan aquí, y ninguna de las
            analizadas lo trae.
          </EmptyState>
        ) : (
          <TimePressureSection buckets={stats.by_time_left} timeTrouble={stats.time_trouble} />
        )}
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Dónde te sales de la teoría</h2>
        <RepertoireSection username={username} />
      </section>

      <section className="space-y-2">
        <h2 className="font-semibold">Por apertura</h2>
        {stats.by_opening.length === 0 ? (
          <EmptyState title="Sin datos de apertura">
            Aquí solo cuentan las partidas que empiezan en la posición estándar: las marcadas como
            «posición dada» no tienen apertura que deducir.
          </EmptyState>
        ) : (
          <DataTable
            headers={[
              ECO_HEADER,
              "Apertura",
              "Color",
              RECORD_HEADER,
              "Puntuación",
              "Precisión",
              OPENING_EXIT_HEADER,
            ]}
          >
            {stats.by_opening.map((item) => (
              <tr key={`${item.opening}-${item.color}`} className={TABLE_ROW_CLASSES}>
                <td className={`font-mono opacity-70 ${TABLE_CELL_CLASSES}`}>{item.eco ?? "—"}</td>
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
                <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
                  {item.average_opening_exit_win_percent === null
                    ? "—"
                    : formatPercent(item.average_opening_exit_win_percent, 1)}
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </section>
    </div>
  );
}

/** Evolución de la precisión y del tipo de errores, mes a mes (RF-3.7).
 *
 * Dos gráficos sobre el mismo eje de meses, que es a propósito el de
 * "Partidas por mes": la precisión (con el rating al lado, para ver si suben
 * juntos) y los errores por tipo. Los errores van **por cada cien jugadas** y
 * no en recuento, porque un mes de cuarenta partidas y otro de cinco no se
 * comparan contando: la línea subiría al jugar más, no al jugar peor.
 */
function TrendsSection({ trends }: { trends: Trends }) {
  const theme = useChartTheme();
  const monthlyChartData = trends.by_month.map((month) => ({
    label: formatYearMonth(month.year, month.month),
    accuracy: month.average_accuracy,
    rating: month.rating,
    ...Object.fromEntries(
      month.mistakes_per_hundred_moves.map((rate) => [rate.mistake_type, rate.per_hundred_moves]),
    ),
  }));
  // Sin un control de tiempo del que hablar no hay serie de rating: dibujarla
  // daría una leyenda "Rating (—)" sobre una línea vacía.
  const ratingLabel = trends.rating_time_class
    ? `Rating (${formatTimeClass(trends.rating_time_class)})`
    : null;
  const legendStyle = { fontSize: 11, color: theme.axisColor };

  return (
    <div className="space-y-3">
      {/* Con un mes analizado no hay comparación posible y los gráficos salen
          con un punto suelto: se dice, en vez de dejar la sección muda. */}
      <p className={`p-2 text-sm ${PANEL_CLASSES}`}>
        {trends.change === null
          ? "Solo hay un mes con partidas analizadas: la comparación aparece en cuanto haya un segundo."
          : formatTrendSentence(trends.change)}
      </p>

      <div className="space-y-1">
        <Panel bodyClassName="h-56 p-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={monthlyChartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="label" tick={theme.axisTickStyle} stroke={theme.axisColor} />
              {/* Dos escalas distintas: la precisión es un porcentaje y el
                  rating son puntos Elo. Compartir eje aplastaría una de las
                  dos contra el borde. */}
              <YAxis
                yAxisId="accuracy"
                domain={[0, 100]}
                tick={theme.axisTickStyle}
                stroke={theme.axisColor}
                width={36}
                unit="%"
              />
              {ratingLabel !== null && (
                <YAxis
                  yAxisId="rating"
                  orientation="right"
                  domain={["dataMin - 50", "dataMax + 50"]}
                  tick={theme.axisTickStyle}
                  stroke={theme.axisColor}
                  width={44}
                />
              )}
              <Tooltip
                contentStyle={theme.tooltipStyle}
                formatter={(value: number, name: string) => [
                  name === ratingLabel ? formatRating(value) : formatPercent(value, 1),
                  name,
                ]}
              />
              <Legend wrapperStyle={legendStyle} />
              <Line
                yAxisId="accuracy"
                type="monotone"
                dataKey="accuracy"
                name="Precisión"
                stroke={theme.seriesColor}
                strokeWidth={2}
                isAnimationActive={false}
              />
              {/* Sin `connectNulls`: un mes sin partidas de ese control deja
                  hueco en vez de inventar una recta entre dos ratings que no
                  se tocaron. */}
              {ratingLabel !== null && (
                <Line
                  yAxisId="rating"
                  type="monotone"
                  dataKey="rating"
                  name={ratingLabel}
                  stroke={theme.ratingColor}
                  strokeWidth={2}
                  strokeDasharray="4 3"
                  isAnimationActive={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </Panel>
        <p className="text-xs opacity-60">
          Precisión media de tus jugadas cada mes
          {ratingLabel !== null && ", con el rating al lado para ver si suben juntos"}. Solo cuentan
          los meses con alguna partida analizada.
        </p>
      </div>

      <div className="space-y-1">
        <Panel bodyClassName="h-56 p-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={monthlyChartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="label" tick={theme.axisTickStyle} stroke={theme.axisColor} />
              <YAxis tick={theme.axisTickStyle} stroke={theme.axisColor} width={36} />
              <Tooltip
                contentStyle={theme.tooltipStyle}
                formatter={(value: number, name: string) => [formatPerHundredMoves(value), name]}
              />
              <Legend wrapperStyle={legendStyle} />
              {/* Apiladas y en orden fijo: la altura total es la tasa de error
                  del mes y cada franja dice de qué tipo. El orden lo fija la
                  API (`MISTAKE_TYPES`), no el reparto del mes. */}
              {trends.by_month[0].mistakes_per_hundred_moves.map((rate) => {
                const style = mistakeTypeStyle(rate.mistake_type);
                return (
                  <Area
                    key={rate.mistake_type}
                    type="monotone"
                    dataKey={rate.mistake_type}
                    name={style.label}
                    stackId="mistakes"
                    stroke={theme.toneColors[style.tone]}
                    fill={theme.toneColors[style.tone]}
                    fillOpacity={0.5}
                    isAnimationActive={false}
                  />
                );
              })}
            </AreaChart>
          </ResponsiveContainer>
        </Panel>
        <p className="text-xs opacity-60">
          Errores por cada cien jugadas tuyas, repartidos por tipo. Normalizado a propósito: en
          recuento crudo la línea subiría al jugar más partidas, no al jugar peor.
        </p>
      </div>

      <DataTable
        headers={[
          "Mes",
          "Partidas",
          "Jugadas",
          "Precisión",
          MISTAKE_RATE_HEADER,
          BLUNDER_RATE_HEADER,
          "Rating",
        ]}
      >
        {trends.by_month.map((month) => (
          <tr key={`${month.year}-${month.month}`} className={TABLE_ROW_CLASSES}>
            <td className={TABLE_CELL_CLASSES}>{formatYearMonth(month.year, month.month)}</td>
            <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>{month.analyzed_games}</td>
            <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>{month.moves}</td>
            <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>
              {formatAccuracy(month.average_accuracy)}
            </td>
            <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>
              {formatPerHundredMoves(
                month.mistakes_per_hundred_moves.reduce(
                  (total, rate) => total + rate.per_hundred_moves,
                  0,
                ),
              )}
            </td>
            <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
              {formatPerHundredMoves(month.blunders_per_hundred_moves)}
            </td>
            <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
              {formatRating(month.rating)}
            </td>
          </tr>
        ))}
      </DataTable>
    </div>
  );
}

function PhaseSection({ phases }: { phases: PhaseStats[] }) {
  const theme = useChartTheme();
  const data = phases.map((phase) => ({
    label: formatPhase(phase.phase),
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
              <XAxis dataKey="label" tick={theme.axisTickStyle} stroke={theme.axisColor} />
              <YAxis
                tick={theme.axisTickStyle}
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

/** Distribución de errores por tipo (RF-3.4).
 *
 * La tabla dice cuántos y de qué tipo; la explicación de cada tipo va debajo,
 * porque "posicional" no significa nada sin la regla con la que se decidió
 * (criterio C-6 de docs/07-coherencia-ui.md).
 */
function MistakeTypeSection({ mistakeTypes }: { mistakeTypes: MistakeTypeStats[] }) {
  const totalMistakes = mistakeTypes.reduce((total, item) => total + item.mistakes, 0);

  return (
    <div className="space-y-2">
      <DataTable headers={["Tipo", "Errores", "De ellos, blunders", "Parte del total"]}>
        {mistakeTypes.map((item) => {
          const style = mistakeTypeStyle(item.mistake_type);
          return (
            <tr key={item.mistake_type} className={TABLE_ROW_CLASSES}>
              <td className={TABLE_CELL_CLASSES}>
                <Badge tone={style.tone} title={style.description}>
                  {style.label}
                </Badge>
              </td>
              <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>{item.mistakes}</td>
              <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>{item.blunders}</td>
              <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>
                {formatPercent((item.mistakes / totalMistakes) * 100)}
              </td>
            </tr>
          );
        })}
      </DataTable>
      <ul className="space-y-0.5 text-xs opacity-60">
        {mistakeTypes.map((item) => {
          const style = mistakeTypeStyle(item.mistake_type);
          return (
            <li key={item.mistake_type}>
              <strong className="font-medium">{style.label}:</strong> {style.description}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** Calidad de juego según el reloj que quedaba (RF-3.5). */
function TimePressureSection({
  buckets,
  timeTrouble,
}: {
  buckets: TimeBucketStats[];
  timeTrouble: TimeTrouble | null;
}) {
  return (
    <div className="space-y-2">
      <DataTable
        headers={["Reloj restante", "Jugadas", "Precisión", "Errores", "De ellos, blunders"]}
      >
        {buckets.map((bucket) => (
          <tr key={String(bucket.max_seconds_left)} className={TABLE_ROW_CLASSES}>
            <td className={TABLE_CELL_CLASSES}>{formatTimeLeftBucket(bucket.max_seconds_left)}</td>
            <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>{bucket.moves}</td>
            <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>
              {formatAccuracy(bucket.average_accuracy)}
            </td>
            <td className={`tabular-nums ${TABLE_CELL_CLASSES}`}>{bucket.mistakes}</td>
            <td className={`tabular-nums opacity-70 ${TABLE_CELL_CLASSES}`}>{bucket.blunders}</td>
          </tr>
        ))}
      </DataTable>
      {timeTrouble !== null && timeTrouble.analyzed_games_with_clocks > 0 && (
        <p className="text-xs opacity-60">
          Llegaste a jugar con menos de veinte segundos en{" "}
          <strong className="font-medium">{timeTrouble.games_in_time_trouble}</strong> de las{" "}
          {timeTrouble.analyzed_games_with_clocks} partidas analizadas con reloj (
          {formatPercent(timeTrouble.share_of_games)}). Solo cuentan las jugadas con reloj
          conocido: una partida sin él no dice nada de esto.
        </p>
      )}
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

