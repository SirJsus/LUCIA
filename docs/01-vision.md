# 01 · Visión

## Problema

Las plataformas de ajedrez (chess.com, lichess, chessable) ofrecen análisis de partidas, estadísticas y entrenamiento, pero:

- Las funciones más útiles (revisión ilimitada de partidas, informe de aperturas, detección de patrones, puzzles personalizados) están detrás de suscripciones.
- El análisis es genérico: no cruza *tu* historial completo para encontrar *tus* debilidades recurrentes.
- No hay control sobre el motor: profundidad, MultiPV, elección Stockfish vs Lc0, ni acceso a los datos crudos.

Los motores que hacen el trabajo pesado (Stockfish, Lc0) son open source y gratuitos. Lo que falta es la capa de lógica y la interfaz.

## Propuesta

**LUCIA** es una aplicación local-first, de un solo usuario (inicialmente), que:

1. **Importa** tu perfil e historial completo de chess.com (API pública, sin login).
2. **Analiza** cada partida con Stockfish (evaluación precisa) y opcionalmente Lc0 (evaluación "posicional", probabilidades de resultado).
3. **Extrae insight**: clasifica jugadas, detecta errores recurrentes por fase/apertura/patrón táctico, mide gestión de tiempo, compara tu repertorio con la teoría.
4. **Entrena**: genera puzzles desde tus propios errores, sparring contra motor calibrado, drills de aperturas donde fallas.
5. **Visualiza** todo en una UI web moderna con tablero interactivo.

## Principios

- **Sin muro de pago, sin nube obligatoria.** Todo corre en tu máquina. Cero costo recurrente.
- **Motores como caja de cristal.** Parámetros expuestos, resultados crudos accesibles, exportables a PGN.
- **Datos propios.** Base de datos local con todo tu historial y análisis; puedes consultarla con SQL.
- **Open source, GPL-3.0.** Compatible con las licencias de los motores.
- **Pragmatismo técnico.** Python para orquestar, C++ solo donde el rendimiento lo exija (ver [ADR-0003](adr/0003-python-orquesta-cpp-motores.md)).

## Fuera de alcance (por ahora)

- Jugar online contra humanos.
- Multiusuario / cuentas / despliegue SaaS.
- Móvil nativo (la web será responsive).
- Entrenar redes neuronales propias.
