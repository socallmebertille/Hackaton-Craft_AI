"""
Utilitaires pour la gestion des tokens JWT
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import JWTError, jwt

# Configuration JWT depuis les variables d'environnement
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un JWT access token

    Args:
        data: Dictionnaire contenant les données à encoder dans le token (user_id, email, role)
        expires_delta: Durée de validité du token (optionnel)

    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()

    # Définir la date d'expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    # Ajouter les claims standards JWT
    to_encode.update({
        "exp": expire,  # Expiration
        "iat": datetime.now(timezone.utc),  # Issued at
    })

    # Encoder le token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Décode et vérifie un JWT access token

    Args:
        token: Token JWT à décoder

    Returns:
        Dictionnaire contenant les données du token si valide, None sinon
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[Dict]:
    """
    Vérifie la validité d'un token JWT

    Args:
        token: Token JWT à vérifier

    Returns:
        Payload du token si valide, None sinon
    """
    return decode_access_token(token)
