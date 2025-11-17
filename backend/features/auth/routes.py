"""
Routes API pour la feature Auth
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db, hash_password, verify_password, User
from .schemas import SignupRequest, LoginRequest
from .service import create_token
from .dependencies import get_current_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post('/signup')
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Inscription d'un nouvel utilisateur (role=0 par défaut, en attente de validation)"""
    # Vérifier que les CGU et la politique de confidentialité sont acceptées
    if not payload.cgu_accepted or not payload.privacy_policy_accepted:
        raise HTTPException(
            status_code=400,
            detail='Vous devez accepter les conditions d\'utilisation et la politique de confidentialité'
        )

    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Un utilisateur avec cet email existe déjà')

    # Hasher le mot de passe avec bcrypt
    password_hash_value = hash_password(payload.password)

    # Créer le nouvel utilisateur (role=0 par défaut)
    new_user = User(
        email=payload.email,
        password_hash=password_hash_value,
        role=0,  # En attente de validation
        cgu_accepted=payload.cgu_accepted,
        privacy_policy_accepted=payload.privacy_policy_accepted,
        consent_date=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Générer le JWT token après la création (besoin de l'ID)
    token = create_token(new_user.id, new_user.email, new_user.role)

    return {
        'token': token,
        'user': new_user.to_dict()
    }


@router.post('/login')
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Connexion d'un utilisateur"""
    # Rechercher l'utilisateur par email
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=401, detail='Email ou mot de passe invalide')

    # Vérifier le mot de passe avec bcrypt
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Email ou mot de passe invalide')

    # Permettre la connexion même pour role=0 (en attente de validation)
    # Le frontend gérera l'affichage approprié selon le rôle

    # Générer un nouveau JWT token
    token = create_token(user.id, user.email, user.role)

    return {
        'token': token,
        'user': user.to_dict()
    }


@router.get('/me')
async def me(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Récupère l'utilisateur courant à partir du JWT token"""
    return {
        'user': user.to_dict()
    }
