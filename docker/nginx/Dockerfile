# ─── Nginx Dockerfile ──────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove default nginx configurations
RUN rm -rf /etc/nginx/conf.d/*

# Copy new optimized configuration
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
