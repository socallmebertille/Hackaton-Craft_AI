"""
Configuration centralisée de l'application
Utilise pydantic-settings pour la validation des variables d'environnement
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Configuration de l'application
    Les valeurs sont chargées depuis les variables d'environnement ou .env
    """

    # Application
    APP_NAME: str = "Juridique AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str
    DEBUG: bool = True

    # Database PostgreSQL - TOUTES les valeurs viennent de l'env
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # Database URL construite automatiquement
    @property
    def DATABASE_URL(self) -> str:
        """Construit l'URL de connexion PostgreSQL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    # Security - DOIVENT être définies dans .env
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Chat settings
    CHAT_INACTIVITY_HOURS: int = 24

    # Email (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = "Juridique AI"

    # Frontend URL (pour les liens de vérification email)
    FRONTEND_URL: str = "http://localhost:5173"

    # Admin account (créé automatiquement au démarrage)
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None
    ADMIN_PRENOM: Optional[str] = "Admin"
    ADMIN_NOM: Optional[str] = "System"
    ADMIN_ENTREPRISE: Optional[str] = "Juridique AI"

    # CraftAI Pipelines
    PIPELINE_0_ENDPOINT_URL: Optional[str] = None  # Analyse d'intention
    PIPELINE_0_ENDPOINT_TOKEN: Optional[str] = None

    PIPELINE_1_ENDPOINT_URL: Optional[str] = None  # Extraction Légifrance
    PIPELINE_1_ENDPOINT_TOKEN: Optional[str] = None

    PIPELINE_3_ENDPOINT_URL: Optional[str] = None  # Débat juridique
    PIPELINE_3_ENDPOINT_TOKEN: Optional[str] = None

    PIPELINE_4_ENDPOINT_URL: Optional[str] = None  # Citations avec explications
    PIPELINE_4_ENDPOINT_TOKEN: Optional[str] = None

    # Légifrance API
    MIBS_LEGIFRANCE_CLIENT_ID: Optional[str] = None
    MIBS_LEGIFRANCE_CLIENT_SECRET: Optional[str] = None
    MIBS_LEGIFRANCE_TOKEN_URL: Optional[str] = None
    MIBS_LEGIFRANCE_API_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instance globale des settings
settings = Settings()
