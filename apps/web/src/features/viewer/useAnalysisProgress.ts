/** Sigue el progreso de un análisis por WebSocket (RF-2.4).
 *
 * El WebSocket es la vía rápida, pero no la única fuente de verdad: si la
 * conexión se cae o el análisis ya había terminado antes de conectar, se
 * refresca la consulta HTTP, que siempre tiene el estado real
 * (ver el docstring de `analysis_progress` en la API).
 */
import type { AnalysisProgressEvent } from "@lucia/shared-types";
import { useEffect, useState } from "react";
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

  useEffect(() => {
    if (analysisId === null) {
      setProgress(null);
      return;
    }

    const socket = new WebSocket(analysisProgressUrl(analysisId));

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as AnalysisProgressEvent;
      if (data.status === "running") {
        setProgress({ ply: data.ply, total: data.total });
      } else {
        setProgress(null);
        onFinished();
      }
    };

    // Si el socket falla (backend caído, proxy mal configurado), no dejamos la
    // UI colgada en "analizando": se consulta el estado por HTTP.
    socket.onerror = () => {
      setProgress(null);
      onFinished();
    };

    return () => {
      setProgress(null);
      socket.close();
    };
  }, [analysisId, onFinished]);

  return progress;
}
