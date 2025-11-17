"""
Dépendances pour l'authentification
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from db import get_db, User
from utils import decode_access_token


def extract_token_from_header_or_query(
    authorization: Optional[str],
    token: Optional[str]
) -> str:
    """Extrait le token depuis le header Authorization ou le paramètre de requête (fonction pure)"""
    # Essayer d'abord le header Authorization
    if authorization:
        # Format: "Bearer <token>"
        if authorization.startswith("Bearer "):
            return authorization[7:]  # Enlever "Bearer "
        return authorization

    # Sinon, utiliser le paramètre de requête (compatibilité ascendante)
    if token:
        return token

    raise HTTPException(status_code=401, detail='Token manquant')


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None
) -> User:
    """Récupère l'utilisateur courant à partir du JWT token"""
    # Extraire le token
    token_value = extract_token_from_header_or_query(authorization, token)

    # Décoder le JWT token
    payload = decode_access_token(token_value)
    if not payload:
        raise HTTPException(status_code=401, detail='Token invalide ou expiré')

    # Récupérer l'ID utilisateur depuis le payload
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='Token invalide')

    # Récupérer l'utilisateur depuis la base de données
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail='Utilisateur non trouvé')

    return user


def require_admin(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None
) -> User:
    """Vérifie que l'utilisateur est admin (role=2)"""
    user = get_current_user(db, authorization, token)

    if user.role != 2:
        raise HTTPException(status_code=403, detail='Accès refusé : droits administrateur requis')

    return user
