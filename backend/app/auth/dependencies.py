"""
Dépendances FastAPI pour l'authentification
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.database.models import User
from app.core.security import decode_access_token
from typing import Optional
import uuid

# Schéma de sécurité Bearer JWT
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur connecté depuis le token JWT

    Args:
        credentials: Token JWT Bearer
        db: Session de base de données

    Returns:
        User: Utilisateur connecté

    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    token = credentials.credentials

    # Décoder le token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extraire l'email du token
    email: str = payload.get("sub")
    user_id_str: str = payload.get("user_id")

    if not email or not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Récupérer l'utilisateur
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé ou en attente de validation"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Récupère l'utilisateur connecté ET vérifie que son email est vérifié

    Args:
        current_user: Utilisateur connecté

    Returns:
        User: Utilisateur connecté avec email vérifié

    Raises:
        HTTPException: Si l'email n'est pas vérifié
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié"
        )

    return current_user
