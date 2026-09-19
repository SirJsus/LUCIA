/** Sigue un análisis en background: su estado y su progreso (RF-2.4).
 *
 * El WebSocket es la vía rápida, pero no la única fuente de verdad: si la
 * conexión se cae o el análisis ya había terminado antes de conectar, se
 * refresca la consulta HTTP, que siempre tiene el estado real
 * (ver el docstring de `analysis_progress` en la API).
 *
 * `onFinished` se guarda en una ref y NO es dependencia del efecto, para que
 * el socket dependa solo del análisis que se está siguiendo. Si fuera
 * dependencia, el socket se cerraría y volvería a abrirse en cada render:
 * quien llama pasa un callback que refresca su propia consulta y cuya
 * identidad cambia siempre — como función en línea por definición, y también
 * envuelto en `useCallback`, porque la dependencia sería el resultado de
 * `useQuery` y react-query devuelve un objeto nuevo (un `Proxy`) en cada
 * render. Ese era el bug de la barra de progreso (RF-2.4): cada evento
 * provocaba un render, ese render reconstruía el socket, y la limpieza del
 * efecto borraba el progreso recién recibido, así que la barra se quedaba
 * clavada en cero y los eventos publicados mientras no había socket se
 * perdían para siempre.
 *
 * Lo consumen `GameViewerPage`, que dibuja la barra junto al reloj de tiempo
 * transcurrido (`useElapsedSeconds`, allí mismo) —esto cuenta posiciones y
 * aquello cuenta segundos, que no son proporcionales entre sí—, y
 * `BoardPage` al analizar un tablero (RF-6.9). Vive en `lib/` y no en una de
 * las dos pantallas porque el análisis en background es el mismo para las
 * dos: lo único que cambia es de dónde salieron las jugadas.
 */
import type { AnalysisProgressEvent } from "@lucia/shared-types";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { analysisProgressUrl, api } from "./api";

export interface AnalysisProgress {
  ply: number;
  total: number;
}

/** El análisis que se está siguiendo, si hay alguno, con su progreso.
 *
 * Quien llama solo pone el id: el estado se consulta por HTTP, el progreso
 * llega por el socket mientras el análisis corre, y al terminar se refresca
 * la consulta sola. Lo comparten el visor de partidas y el tablero de
 * análisis (RF-6.9), que siguen análisis idénticos salvo por de dónde
 * salieron las jugadas.
 */
export function useTrackedAnalysis(analysisId: number | null) {
  const query = useQuery({
    queryKey: ["analysis", analysisId],
    queryFn: () => api.getAnalysis(analysisId as number),
    enabled: analysisId !== null,
  });
  const analysis = query.data;
  const isRunning = analysis?.status === "queued" || analysis?.status === "running";
  const progress = useAnalysisProgress(isRunning ? analysisId : null, () => query.refetch());
  return { analysis, isRunning, progress };
}

function useAnalysisProgress(
  analysisId: number | null,
  onFinished: () => void,
): AnalysisProgress | null {
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  const onFinishedRef = useRef(onFinished);
  onFinishedRef.current = onFinished;

  useEffect(() => {
    if (analysisId === null) {
      setProgress(null);
      return;
    }

    const socket = new WebSocket(analysisProgressUrl(analysisId));

    function finish() {
      setProgress(null);
      onFinishedRef.current();
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as AnalysisProgressEvent;
      if (data.status === "running") setProgress({ ply: data.ply, total: data.total });
      else finish();
    };

    // Si el socket falla (backend caído, proxy mal configurado), no dejamos la
    // UI colgada en "analizando": se consulta el estado por HTTP.
    socket.onerror = finish;

    return () => {
      setProgress(null);
      socket.close();
    };
  }, [analysisId]);

  return progress;
}

/** Segundos que lleva corriendo el análisis, mientras `isRunning` sea cierto.
 *
 * Acompaña a la barra de progreso en vez de sustituirla porque miden cosas
 * distintas: la barra va por posición evaluada, y esas no tardan lo mismo —
 * las que ya están en `position_cache` salen al instante y Lc0 tarda distinto
 * en cada una. El reloj es lo único que dice cuánto se lleva esperado de
 * verdad. Cuenta desde que esta pantalla ve el análisis en marcha, así que al
 * recargar la página empieza de cero; para que sobreviviera habría que
 * exponer `created_at` de la fila `analyses`, que hoy no sale en la API.
 */
export function useElapsedSeconds(isRunning: boolean): number {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!isRunning) {
      setElapsedSeconds(0);
      return;
    }
    const startedAt = Date.now();
    const timer = setInterval(
      () => setElapsedSeconds(Math.round((Date.now() - startedAt) / 1000)),
      1000,
    );
    return () => clearInterval(timer);
  }, [isRunning]);

  return elapsedSeconds;
}
