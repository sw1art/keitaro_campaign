# ---- Build stage ----
FROM node:24-alpine AS build

WORKDIR /app

# Public runtime config is inlined at BUILD time for an SPA, so expose it as
# build args (defaults match the local docker-compose setup).
ARG NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
ARG NUXT_PUBLIC_API_TOKEN=
ARG NUXT_PUBLIC_MOCK=false
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE \
    NUXT_PUBLIC_API_TOKEN=$NUXT_PUBLIC_API_TOKEN \
    NUXT_PUBLIC_MOCK=$NUXT_PUBLIC_MOCK

# Install dependencies first so this layer is cached.
COPY package.json ./
COPY package-lock.json ./
RUN npm ci

# Copy the rest of the sources and build the SPA.
COPY . .
RUN npm run build

# ---- Runtime stage ----
FROM node:24-alpine

WORKDIR /app

ENV NODE_ENV=production

COPY --from=build /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
