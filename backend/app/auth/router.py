"""
Routes d'authentification - Endpoints API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.database.models import User
from app.auth import schemas, service, dependencies

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: schemas.UserRegister,
    db: Session = Depends(get_db)
):
    """
    Inscription d'un nouveau utilisateur

    - **prenom**: Prénom de l'utilisateur
    - **nom**: Nom de l'utilisateur
    - **entreprise**: Nom de l'entreprise
    - **email**: Email (doit être unique)
    - **password**: Mot de passe (min 8 caractères)

    Un email de vérification sera envoyé à l'adresse fournie.
    Retourne les informations de l'utilisateur créé (sans le mot de passe).
    """
    user = await service.create_user(db, user_data)
    return user


@router.post("/login", response_model=schemas.TokenWithUser)
async def login(
    credentials: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """
    Connexion d'un utilisateur

    - **email**: Email de l'utilisateur
    - **password**: Mot de passe

    Retourne un token JWT et les informations utilisateur.
    """
    user = service.authenticate_user(db, credentials.email, credentials.password)
    access_token = service.create_user_token(user)

    return schemas.TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user)
    )


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Vérifie l'email d'un utilisateur via le token envoyé par email

    - **token**: Token de vérification reçu par email

    Active le compte et permet la connexion.
    """
    user = service.verify_email_token(db, token)

    return {
        "message": "Email vérifié avec succès",
        "email": user.email,
        "verified": True
    }


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(dependencies.get_current_user)
):
    """
    Récupère les informations de l'utilisateur connecté

    Requiert un token JWT valide dans le header Authorization: Bearer <token>
    """
    return current_user


@router.get("/account-status")
async def check_account_status(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Vérifie le statut d'activation d'un compte par email

    - **email**: Email de l'utilisateur

    Retourne l'état du compte (is_active, email_verified).
    Utile pour informer l'utilisateur avant qu'il ne tente de se connecter.
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    return {
        "email": user.email,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "status_message": (
            "Compte actif" if user.is_active and user.email_verified
            else "Email non vérifié" if not user.email_verified
            else "En attente de validation administrateur"
        )
    }


@router.delete("/account")
async def delete_account(
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime le compte de l'utilisateur connecté

    Requiert un token JWT valide dans le header Authorization: Bearer <token>

    ATTENTION: Cette action est irréversible et supprime:
    - Le compte utilisateur
    - Tous les chats associés (cascade)
    - Tous les messages associés (cascade)
    """
    user_email = current_user.email

    # Supprimer l'utilisateur (cascade supprime automatiquement les chats et messages)
    db.delete(current_user)
    db.commit()

    return {
        "message": "Compte supprimé avec succès",
        "email": user_email
    }
