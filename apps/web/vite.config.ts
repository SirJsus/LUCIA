import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El puerto de la API se puede cambiar para convivir con otros proyectos en la
// misma máquina (`API_PORT=8001 make up`); `scripts/dev.sh` exporta la misma
// variable, así que el proxy y la API no se pueden desincronizar.
const API_PORT = process.env.API_PORT ?? "8000";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Separa las librerías pesadas del código propio: cambian mucho menos
        // a menudo, así el navegador puede cachearlas entre despliegues.
        // React queda con el código de la app a propósito: separarlo creaba
        // un ciclo entre chunks (recharts importa react y viceversa a través
        // de código compartido), y Vite avisa de ello.
        manualChunks: {
          chess: ["chess.js", "chessground"],
          charts: ["recharts"],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: `http://localhost:${API_PORT}`,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      "/ws": { target: `ws://localhost:${API_PORT}`, ws: true },
    },
  },
});
