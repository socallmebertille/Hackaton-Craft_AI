"""
Backend FastAPI - Juridique AI
API minimaliste pour démarrage du projet
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Juridique AI - API",
    description="API pour l'assistant juridique basé sur l'IA",
    version="1.0.0"
)

# Configuration CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative
        "http://localhost:8001",  # Frontend docker
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint racine - Health check"""
    return {
        "message": "Juridique AI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health():
    """Endpoint de santé"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/test")
async def test():
    """Endpoint de test"""
    return {
        "message": "Backend opérationnel !",
        "test": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
