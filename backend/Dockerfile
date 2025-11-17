# Dockerfile de production pour le backend FastAPI
# Multi-stage build pour réduire la taille de l'image finale

# ========== STAGE 1: Builder ==========
FROM python:3.11-slim as builder

WORKDIR /app

# Installer les dépendances système pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt
COPY ../requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --user -r requirements.txt

# ========== STAGE 2: Runtime ==========
FROM python:3.11-slim

WORKDIR /app

# Créer utilisateur non-root (UID 1000 pour correspondre à l'utilisateur hôte)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copier les dépendances depuis builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Ajouter au PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Copier le code source
COPY --chown=appuser:appuser . .

# Utilisateur non-root
USER appuser

# Démarrage production - Les variables HOST, PORT et WORKERS seront définies via .env
CMD uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --workers ${WORKERS:-4}
