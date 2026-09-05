FROM node:22-alpine AS build
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY apps/web apps/web
COPY packages/shared-types packages/shared-types
RUN pnpm install --frozen-lockfile && pnpm build:web

FROM nginx:alpine
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
