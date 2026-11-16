# ---- Build stage ----
FROM node:24-alpine AS build

WORKDIR /app

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
# Default API base; override at runtime with the same env name if you
# rebuild, or bake it in at build time (SPA public config is inlined).
ENV NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1

COPY --from=build /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
