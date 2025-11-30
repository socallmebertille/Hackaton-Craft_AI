"""
Service d'authentification - Logique métier
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.database.models import User
from app.auth.schemas import UserRegister, UserLogin
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    validate_email, validate_name, validate_company_name,
    validate_password_strength, validate_input_security
)
from app.core.email import send_email, generate_verification_email
from datetime import timedelta, datetime
from app.core.config import settings
import secrets


async def create_user(db: Session, user_data: UserRegister) -> User:
    """
    Crée un nouveau utilisateur et envoie un email de vérification

    Args:
        db: Session de base de données
        user_data: Données de l'utilisateur à créer

    Returns:
        User: Utilisateur créé

    Raises:
        HTTPException: Si l'email existe déjà ou si les données sont invalides
    """
    # ===== VALIDATION ET SANITIZATION DES INPUTS =====

    # Valider et nettoyer l'email
    clean_email = validate_email(user_data.email)

    # Valider et nettoyer le prénom
    clean_prenom = validate_name(user_data.prenom, "prénom")

    # Valider et nettoyer le nom
    clean_nom = validate_name(user_data.nom, "nom")

    # Valider et nettoyer le nom d'entreprise
    clean_entreprise = validate_company_name(user_data.entreprise)

    # Valider la sécurité générale de tous les champs
    validate_input_security(clean_prenom, "prénom")
    validate_input_security(clean_nom, "nom")
    validate_input_security(clean_entreprise, "entreprise")

    # Valider la force du mot de passe
    validate_password_strength(user_data.password)

    # ===== FIN VALIDATION =====

    # Vérifier si l'email existe déjà (avec l'email nettoyé)
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte existe déjà avec cet email"
        )

    # Générer le token de vérification
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.utcnow() + timedelta(hours=24)

    # Créer le nouvel utilisateur avec les données nettoyées
    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        prenom=clean_prenom,
        nom=clean_nom,
        entreprise=clean_entreprise,
        email=clean_email,
        hashed_password=hashed_password,
        is_active=False,  # Compte inactif par défaut, nécessite validation admin
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=verification_expires
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Envoyer l'email de vérification
    html_content, text_content = generate_verification_email(new_user.email, verification_token)
    try:
        await send_email(
            to_emails=[new_user.email],
            subject="Vérifiez votre email - Juridique AI",
            html_content=html_content,
            text_content=text_content
        )
    except Exception as e:
        print(f"⚠️ Erreur envoi email de vérification: {e}")
        # On ne bloque pas l'inscription si l'email échoue

    return new_user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authentifie un utilisateur

    Args:
        db: Session de base de données
        email: Email de l'utilisateur
        password: Mot de passe en clair

    Returns:
        User: Utilisateur authentifié

    Raises:
        HTTPException: Si les credentials sont invalides
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié. Veuillez vérifier votre email avant de vous connecter."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte en attente de validation par un administrateur. Vous recevrez un email une fois validé."
        )

    return user


def verify_email_token(db: Session, token: str) -> User:
    """
    Vérifie un token d'email et active le compte

    Args:
        db: Session de base de données
        token: Token de vérification

    Returns:
        User: Utilisateur vérifié

    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    user = db.query(User).filter(User.verification_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de vérification invalide"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà vérifié"
        )

    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de vérification expiré"
        )

    # Marquer l'email comme vérifié
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None

    db.commit()
    db.refresh(user)

    return user


def create_user_token(user: User) -> str:
    """
    Crée un token JWT pour un utilisateur

    Args:
        user: Utilisateur pour lequel créer le token

    Returns:
        str: Token JWT
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )

    return access_token
