"""
Sécurité - Hashing de mots de passe, JWT et validation des inputs
Protection contre les injections SQL et XSS
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import settings
import re
import html

# Configuration pour le hashing de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond au hash

    Args:
        plain_password: Mot de passe en clair
        hashed_password: Mot de passe hashé

    Returns:
        bool: True si le mot de passe correspond
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash un mot de passe avec bcrypt

    Args:
        password: Mot de passe en clair

    Returns:
        str: Mot de passe hashé

    Raises:
        HTTPException: Si le mot de passe dépasse 72 octets
    """
    # Vérification de sécurité : bcrypt limite à 72 octets
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le mot de passe est trop long ({len(password_bytes)} octets, maximum 72 octets)"
        )

    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT

    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité du token

    Returns:
        str: Token JWT encodé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Décode un token JWT

    Args:
        token: Token JWT à décoder

    Returns:
        dict: Données contenues dans le token ou None si invalide
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# ============================================================================
# Validation et sanitization des inputs - Protection XSS et SQL Injection
# ============================================================================

def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize une chaîne de caractères pour prévenir les attaques XSS

    Args:
        value: La chaîne à nettoyer
        max_length: Longueur maximale autorisée

    Returns:
        str: La chaîne nettoyée

    Raises:
        HTTPException: Si la validation échoue
    """
    if not value:
        return value

    # Vérifier la longueur
    if len(value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le champ ne peut pas dépasser {max_length} caractères"
        )

    # Échapper les caractères HTML pour prévenir XSS
    sanitized = html.escape(value.strip())

    return sanitized


def validate_email(email: str) -> str:
    """
    Valide et nettoie une adresse email

    Args:
        email: L'adresse email à valider

    Returns:
        str: L'email nettoyé en minuscules

    Raises:
        HTTPException: Si l'email est invalide
    """
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'adresse email est requise"
        )

    # Pattern pour valider l'email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    email = email.strip().lower()

    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'email invalide"
        )

    if len(email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'adresse email est trop longue"
        )

    return email


def validate_name(name: str, field_name: str = "nom") -> str:
    """
    Valide un nom (prénom, nom de famille)

    Args:
        name: Le nom à valider
        field_name: Le nom du champ pour les messages d'erreur

    Returns:
        str: Le nom nettoyé

    Raises:
        HTTPException: Si le nom est invalide
    """
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le {field_name} est requis"
        )

    name = name.strip()

    # Vérifier la longueur
    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le {field_name} doit contenir au moins 2 caractères"
        )

    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le {field_name} ne peut pas dépasser 100 caractères"
        )

    # Autoriser uniquement lettres, espaces, tirets et apostrophes
    if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le {field_name} contient des caractères invalides"
        )

    # Échapper les caractères HTML
    return html.escape(name)


def validate_company_name(company: str) -> str:
    """
    Valide un nom d'entreprise

    Args:
        company: Le nom de l'entreprise à valider

    Returns:
        str: Le nom d'entreprise nettoyé

    Raises:
        HTTPException: Si le nom est invalide
    """
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom de l'entreprise est requis"
        )

    company = company.strip()

    if len(company) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom de l'entreprise doit contenir au moins 2 caractères"
        )

    if len(company) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom de l'entreprise ne peut pas dépasser 200 caractères"
        )

    # Autoriser lettres, chiffres, espaces et quelques caractères spéciaux
    if not re.match(r"^[a-zA-Z0-9À-ÿ\s\-'.&()]+$", company):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom de l'entreprise contient des caractères invalides"
        )

    return html.escape(company)


def validate_password_strength(password: str) -> None:
    """
    Valide la force d'un mot de passe

    Args:
        password: Le mot de passe à valider

    Raises:
        HTTPException: Si le mot de passe ne respecte pas les critères
    """
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe est requis"
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 8 caractères"
        )

    # Vérifier la limite de bcrypt (72 octets maximum)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le mot de passe est trop long ({len(password_bytes)} octets, maximum 72 octets pour bcrypt)"
        )

    # Vérifier la complexité
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))

    if not (has_upper and has_lower and has_digit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins une majuscule, une minuscule et un chiffre"
        )


def validate_integer(value: Optional[int], min_value: int = 1, max_value: int = 10000, field_name: str = "valeur") -> Optional[int]:
    """
    Valide un entier dans une plage donnée

    Args:
        value: La valeur à valider
        min_value: Valeur minimale autorisée
        max_value: Valeur maximale autorisée
        field_name: Le nom du champ pour les messages d'erreur

    Returns:
        int: La valeur validée

    Raises:
        HTTPException: Si la valeur est invalide
    """
    if value is None:
        return None

    if not isinstance(value, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le {field_name} doit être un nombre entier"
        )

    if value < min_value or value > max_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le {field_name} doit être entre {min_value} et {max_value}"
        )

    return value


def detect_sql_injection(value: str) -> bool:
    """
    Détecte les tentatives d'injection SQL

    Args:
        value: La chaîne à vérifier

    Returns:
        bool: True si une injection SQL est détectée
    """
    if not value:
        return False

    # Patterns courants d'injection SQL
    sql_patterns = [
        r"(\s|^)(union|select|insert|update|delete|drop|create|alter|exec|execute)(\s|$)",
        r"(\s|^)(or|and)(\s+)(\d+)(\s*)=(\s*)(\d+)",
        r"[;'](\s*)(union|select|insert|update|delete|drop)",
        r"--",
        r"/\*",
        r"\*/",
        r"xp_",
        r"sp_",
        r"0x[0-9a-f]+",
    ]

    value_lower = value.lower()

    for pattern in sql_patterns:
        if re.search(pattern, value_lower):
            return True

    return False


def detect_xss(value: str) -> bool:
    """
    Détecte les tentatives d'attaque XSS

    Args:
        value: La chaîne à vérifier

    Returns:
        bool: True si un XSS est détecté
    """
    if not value:
        return False

    # Patterns courants d'XSS
    xss_patterns = [
        r"<script",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    value_lower = value.lower()

    for pattern in xss_patterns:
        if re.search(pattern, value_lower):
            return True

    return False


def validate_input_security(value: str, field_name: str = "champ") -> str:
    """
    Validation de sécurité générale pour tous les inputs

    Args:
        value: La valeur à valider
        field_name: Le nom du champ pour les messages d'erreur

    Returns:
        str: La valeur validée

    Raises:
        HTTPException: Si une menace de sécurité est détectée
    """
    if not value:
        return value

    # Détecter les injections SQL
    if detect_sql_injection(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Caractères suspects détectés dans le {field_name}"
        )

    # Détecter les scripts XSS
    if detect_xss(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contenu non autorisé détecté dans le {field_name}"
        )

    return value
