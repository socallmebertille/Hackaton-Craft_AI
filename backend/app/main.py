"""
Backend FastAPI - Juridique AI
Point d'entrée principal de l'application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.base import engine
from app.database.models import Base
from app.auth.router import router as auth_router
from app.admin.router import router as admin_router
from app.chat.router import router as chat_router


# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API pour l'assistant juridique basé sur l'IA"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup_event():
    """
    Événement exécuté au démarrage de l'application
    """
    print(f"🚀 Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environnement: {settings.ENVIRONMENT}")
    print(f"🗄️  Base de données: {settings.POSTGRES_DB}")

    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    print("✅ Tables de base de données vérifiées")

    # Créer le compte administrateur si configuré
    from app.database.init_db import create_admin_user
    create_admin_user()


@app.get("/")
async def root():
    """Endpoint racine - Health check"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/health")
async def health():
    """Endpoint de santé avec informations détaillées"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": settings.POSTGRES_DB,
        "version": settings.APP_VERSION
    }


@app.get("/api/test-db")
async def test_db():
    """Test de connexion à la base de données"""
    from app.database.base import SessionLocal
    from app.database.models import User, Chat

    try:
        db = SessionLocal()
        # Compter les utilisateurs et les chats
        user_count = db.query(User).count()
        chat_count = db.query(Chat).count()
        db.close()

        return {
            "status": "success",
            "message": "Connexion à la base de données réussie",
            "user_count": user_count,
            "chat_count": chat_count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur de connexion: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
