"""
API REST pour l'Assistant Juridique à base de débat LLM

Cette API FastAPI expose les endpoints permettant de:
1. Soumettre une question juridique et lancer un débat
2. Suivre l'état d'avancement d'un débat
3. Récupérer les résultats complets d'un débat terminé
4. Gérer la liste des débats
5. Gérer l'authentification et les utilisateurs
6. Administrer les utilisateurs (panel admin)

Architecture:
- Frontend (Vue.js) -> API REST (FastAPI) -> Services (3 Pipelines CraftAI)
- Traitement asynchrone via BackgroundTasks pour ne pas bloquer l'API
- Architecture modulaire par features (auth, user, admin, debate)
- Base de données PostgreSQL pour les utilisateurs
- Authentification JWT

Pipelines CraftAI:
- Pipeline 1: Extraction des concepts juridiques
- Pipeline 2: Recherche des articles sur Légifrance
- Pipeline 3: Génération du débat contradictoire
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_database

# Import des routers des différentes features
from features.auth import router as auth_router
from features.user import router as user_router
from features.admin import router as admin_router
from features.debate import router as debate_router

# ========== INITIALISATION DE L'APPLICATION ==========

app = FastAPI(
    title="Assistant Juridique - Débat LLM",
    description="API de débat contradictoire entre LLM sur des questions juridiques",
    version="2.0.0"
)

# ========== ÉVÉNEMENT DE DÉMARRAGE ==========

@app.on_event("startup")
async def startup_event():
    """Initialise la base de données au démarrage de l'application"""
    print("\n🚀 Démarrage de l'application...")
    init_database()
    print("✅ Application prête !\n")

# ========== CONFIGURATION CORS ==========

# Configuration CORS sécurisée pour éviter les attaques cross-origin
# IMPORTANT: En production, remplacer par votre domaine réel (https://yourdomain.com)

# Liste des origines autorisées (whitelist)
allowed_origins = [
    "http://localhost:5173",    # Vite (dev frontend)
    "http://localhost:3000",    # React/Next.js standard
    "http://localhost:8080",    # Vue CLI / alternatives
    "http://localhost:8001",    # Port utilisé par le frontend actuel
    "http://localhost:80",      # Nginx Docker
    "http://localhost",         # Nginx Docker (sans port)
    "http://127.0.0.1:8080",    # Variante 127.0.0.1
    "http://127.0.0.1:80",      # Variante 127.0.0.1 nginx (avec port)
    "http://127.0.0.1:8001",    # Variante 127.0.0.1 frontend
    "http://127.0.0.1",         # Variante 127.0.0.1 sans port
]

# En production, ajouter le domaine de production depuis les variables d'environnement
production_origin = os.getenv("PRODUCTION_ORIGIN")
if production_origin:
    allowed_origins.append(production_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    # SÉCURITÉ: Limiter aux méthodes HTTP nécessaires au lieu de "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # SÉCURITÉ: Limiter aux headers nécessaires au lieu de "*"
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
    # Exposer les headers nécessaires au frontend
    expose_headers=["Content-Type", "Authorization"],
    # Durée de cache pour les preflight requests (OPTIONS)
    max_age=600,  # 10 minutes
)

# ========== ENREGISTREMENT DES ROUTERS ==========

# Enregistrer les routers de chaque feature

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(debate_router)

# ========== ENDPOINT RACINE ==========

@app.get("/")
async def root():
    """
    Endpoint racine - Informations sur l'API
    Retourne les métadonnées de l'API et la liste des endpoints disponibles.
    Utile pour vérifier que le serveur est démarré.

    Returns:
        Dict: Informations sur l'API et ses endpoints

    Example:
        GET http://localhost:8000/
        Response:
        {
            "message": "Assistant Juridique API - Débat LLM",
            "version": "2.0.0",
            "endpoints": {...}
        }
    """
    return {
        "message": "Assistant Juridique API - Débat LLM",
        "version": "2.0.0",
        "features": {
            "auth": "Authentification (signup, login, me)",
            "user": "Gestion du profil utilisateur",
            "admin": "Panel d'administration",
            "debate": "Débats juridiques contradictoires"
        },
        "endpoints": {
            "auth": {
                "signup": "/api/auth/signup",
                "login": "/api/auth/login",
                "me": "/api/auth/me"
            },
            "user": {
                "profile": "/api/user/profile",
                "password": "/api/user/password",
                "request_deletion": "/api/user/request-deletion",
                "cancel_deletion": "/api/user/cancel-deletion",
                "delete_account": "/api/user/account"
            },
            "admin": {
                "list_users": "/api/admin/users",
                "list_pending": "/api/admin/users/pending",
                "list_validated": "/api/admin/users/validated",
                "validate_user": "/api/admin/users/{user_id}/validate",
                "delete_user": "/api/admin/users/{user_id}"
            },
            "debate": {
                "submit": "/api/debate/submit",
                "status": "/api/debate/{debate_id}",
                "export_pdf": "/api/debate/{debate_id}/export-pdf",
                "list": "/api/debates",
                "delete": "/api/debate/{debate_id}"
            }
        }
    }


# ========== POINT D'ENTRÉE (DÉVELOPPEMENT) ==========

if __name__ == "__main__":
    """
    Lance le serveur Uvicorn en mode développement

    Commande équivalente en CLI:
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload

    En production, utiliser plutôt:
        gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
    """
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",  # Écouter sur toutes les interfaces (accessible depuis réseau)
        port=8000        # Port par défaut
    )
