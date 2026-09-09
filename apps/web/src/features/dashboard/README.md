# `features/dashboard`

Estadísticas de la práctica propia (RF-3.1 a RF-3.3): marcador y rating por
control de tiempo, partidas por mes, rendimiento por apertura y pérdida de
ventaja por fase. Todo se agrega en la API (`GET /stats/...`); aquí solo se
presenta.

Las dos tablas salen de `components/DataTable` y los tres gráficos de
**Recharts**, que pinta ejes y tooltip con estilos en línea y por eso necesita
la paleta como valores concretos: se la da `lib/chartTheme.ts`, que sigue el
tema claro/oscuro activo.
