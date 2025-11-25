# Frontend Dockerfile for Meru Coders - Sanskrit Meter Identification System
FROM nginx:alpine

# Copy frontend files to nginx html directory
COPY frontend/ /usr/share/nginx/html/

# Copy custom nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
