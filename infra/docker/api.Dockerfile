# Etapa 1: compilar Stockfish (Lc0 se añade en Fase 2; requiere meson/ninja/blas)
FROM debian:bookworm-slim AS engines
RUN apt-get update && apt-get install -y --no-install-recommends git make g++ ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN git clone --depth 1 --branch sf_17.1 https://github.com/official-stockfish/Stockfish.git \
 && make -C Stockfish/src -j"$(nproc)" build ARCH=x86-64-avx2

# Etapa 2: API
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY --from=engines /src/Stockfish/src/stockfish /app/engines/bin/stockfish
COPY pyproject.toml uv.lock* ./
COPY apps/api apps/api
COPY packages/core packages/core
COPY packages/chesscom packages/chesscom
RUN uv sync --frozen --no-dev
ENV STOCKFISH_PATH=/app/engines/bin/stockfish
EXPOSE 8000
CMD ["uv", "run", "--package", "lucia-api", "uvicorn", "lucia_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
