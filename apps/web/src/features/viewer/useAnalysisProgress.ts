/** Sigue el progreso de un análisis por WebSocket (RF-2.4).
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
 * Lo consume `GameViewerPage`, que dibuja la barra junto al reloj de tiempo
 * transcurrido (`useElapsedSeconds`, allí mismo): esto cuenta posiciones y
 * aquello cuenta segundos, que no son proporcionales entre sí.
 */
import type { AnalysisProgressEvent } from "@lucia/shared-types";
import { useEffect, useRef, useState } from "react";
import { analysisProgressUrl } from "../../lib/api";

export interface AnalysisProgress {
  ply: number;
  total: number;
}

export function useAnalysisProgress(
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
