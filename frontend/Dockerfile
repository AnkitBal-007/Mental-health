# ── Stage 1: Build React SPA bundle ──
FROM node:20-alpine AS builder

WORKDIR /app

# Accept optional build-time environment variables for API routing
ARG VITE_BACKEND_URL=/api
ARG VITE_ML_URL=/ml
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}
ENV VITE_ML_URL=${VITE_ML_URL}

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: Serve static production assets with Nginx ──
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled SPA bundle from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with /api reverse proxy and SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
