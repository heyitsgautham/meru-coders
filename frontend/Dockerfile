# Frontend Dockerfile for Meru Coders - Sanskrit Meter Identification System
# Multi-stage build: Build with Node, serve with Nginx

# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ ./

# Build the app (outputs to /app/build)
RUN npm run build

# scripts/deploy.sh writes config.js with the production API URL before a
# Cloud Run build. Without it, write an empty config so the app falls back
# to http://localhost:5000/api.
RUN test -f config.js || echo "window.CONFIG = window.CONFIG || {};" > config.js

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Runtime config (see the builder stage)
COPY --from=builder /app/config.js /usr/share/nginx/html/config.js

# Expose port 8080 (Cloud Run expects this)
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
