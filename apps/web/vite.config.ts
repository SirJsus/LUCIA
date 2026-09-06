import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

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
      "/api": { target: "http://localhost:8000", rewrite: (p) => p.replace(/^\/api/, "") },
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
