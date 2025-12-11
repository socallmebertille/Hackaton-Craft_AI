# Dockerfile de production pour le frontend Vite + React
# Multi-stage build pour optimiser la taille de l'image finale

# ========== STAGE 1: Builder ==========
FROM node:20-alpine as builder

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances (y compris devDependencies pour le build)
RUN npm install && npm cache clean --force

# Copier le code source
COPY . .

# Build de production
RUN npm run build

# ========== STAGE 2: Production avec Nginx ==========
FROM nginx:alpine

# Copier les fichiers buildés depuis le stage builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier la configuration nginx personnalisée pour gérer le SPA routing
COPY nginx.conf /etc/nginx/nginx.conf

# Exposer le port 80
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Nginx démarre automatiquement
CMD ["nginx", "-g", "daemon off;"]
